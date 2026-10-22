# app/strategy/patterns/rule_engine.py
"""
Safe Rule Engine for YAML-driven Chart & Wave Pattern Classification.

Replaces the legacy raw `eval()` with a whitelisted AST evaluator (no
arbitrary code execution) and produces REAL per-rule evaluation diagnostics
instead of the old hardcoded `passed: True` values.

Key guarantees:
1. Every condition in `pattern_rules.yaml` is parsed into a restricted AST
   supporting only: numeric literals, pattern variables, + - * / ( )
   arithmetic, unary +/- and chained comparisons. Anything else raises
   ``RuleConditionError`` and is logged loudly (never silently ignored).
2. Classification is fully rule-driven: the first YAML pattern definition
   (matching the candidate direction) whose rules ALL pass wins.
3. Every rule evaluation returns a real (passed, value) pair so the UI can
   show honest diagnostics.
4. Detector thresholds (min impulse ATR, max retrace, impulse min pct per
   asset class, ...) come from the YAML ``detector_config`` section, with
   sane built-in defaults.
"""
from __future__ import annotations

import ast
import logging
import operator as op
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import yaml

logger = logging.getLogger("algotrade.strategy.rule_engine")

RULES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "data",
    "pattern_rules.yaml",
)

PATTERN_COLORS = {
    "flag": "#eab308",    # Yellow
    "flat": "#a855f7",    # Purple
    "wedge": "#3b82f6",   # Blue
    "zigzag": "#06b6d4",  # Cyan
}

DEFAULT_DETECTOR_CONFIG = {
    "min_impulse_atr": 1.5,
    "flag_max_retrace": 0.382,
    "flat_max_retrace": 0.70,
    "wave_b_min_retrace": 0.25,
    "min_risk_reward": 1.5,
    "impulse_min_pct_default": 0.018,
    "impulse_min_pct_by_class": {
        "crypto": 0.005,
        "forex": 0.004,
        "metal": 0.008,
        "index": 0.008,
    },
}


class RuleConditionError(Exception):
    """Raised when a YAML rule condition cannot be safely evaluated."""


# ────────────────────────────────────────────────────────────────
# Safe AST-based expression evaluator
# ────────────────────────────────────────────────────────────────
_BIN_OPS: dict = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
}
_UNARY_OPS: dict = {ast.USub: op.neg, ast.UAdd: op.pos, ast.Not: op.not_}
_CMP_OPS: dict = {
    ast.Gt: op.gt,
    ast.GtE: op.ge,
    ast.Lt: op.lt,
    ast.LtE: op.le,
    ast.Eq: op.eq,
    ast.NotEq: op.ne,
}


@lru_cache(maxsize=1024)
def _compile_expression(expr: str) -> ast.expr:
    """Compile a condition expression into a whitelisted AST body."""
    tree = ast.parse(expr, mode="eval")
    return tree.body


def _format_number(value: float) -> str:
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    if abs(value) >= 1:
        return f"{value:.2f}"
    return f"{value:.4f}"


def _compare(left: Any, cmp_op: Any, right: Any) -> bool:
    """Compare two values; float equality uses a small tolerance."""
    if isinstance(left, bool) or isinstance(right, bool):
        return bool(cmp_op(left, right))
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        lf, rf = float(left), float(right)
        if cmp_op is op.eq:
            return abs(lf - rf) < 1e-9
        if cmp_op is op.ne:
            return abs(lf - rf) >= 1e-9
        return bool(cmp_op(lf, rf))
    if cmp_op in (op.eq, op.ne):
        return bool(cmp_op(left, right))
    return False




_BOOL_OPS: dict[type[ast.boolop], Any] = {
    ast.And: lambda values: all(values),
    ast.Or: lambda values: any(values),
}


def _eval_node(node: ast.expr, variables: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, bool)):
            return node.value
        raise RuleConditionError(f"Unsupported constant: {node.value!r}")
    if isinstance(node, ast.Name):
        if node.id in variables:
            return variables[node.id]
        raise RuleConditionError(f"Unknown variable: {node.id}")
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](
            _eval_node(node.left, variables), _eval_node(node.right, variables)
        )
    if isinstance(node, ast.BoolOp) and type(node.op) in _BOOL_OPS:
        return _BOOL_OPS[type(node.op)](
            [_eval_node(val, variables) for val in node.values]
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand, variables))
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, variables)
        for cmp_op, comparator in zip(node.ops, node.comparators, strict=False):
            if type(cmp_op) not in _CMP_OPS:
                raise RuleConditionError(f"Unsupported comparison: {type(cmp_op).__name__}")
            right = _eval_node(comparator, variables)
            if not _compare(left, _CMP_OPS[type(cmp_op)], right):
                return False
            left = right
        return True
    raise RuleConditionError(f"Unsupported expression node: {type(node).__name__}")


def evaluate_expression(expr: str, variables: dict[str, Any]) -> bool:
    """
    Safely evaluate a YAML rule condition against pattern variables.

    Raises:
        RuleConditionError: on syntax errors, unknown variables, or any
            expression construct outside the whitelisted subset.
    """
    expr = (expr or "").strip()
    if not expr:
        return True
    try:
        body = _compile_expression(expr)
        return bool(_eval_node(body, variables))
    except RuleConditionError:
        raise
    except Exception as exc:  # syntax errors, etc.
        raise RuleConditionError(f"Failed to evaluate '{expr}': {exc}") from exc


def _eval_numeric(expr: str, variables: dict[str, Any]) -> float | None:
    """Evaluate an expression to a number for diagnostics; None on failure."""
    try:
        value = _eval_node(_compile_expression(expr.strip()), variables)
        if isinstance(value, bool):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
    except Exception:
        return None
    return None


# ────────────────────────────────────────────────────────────────
# YAML loading (mtime-cached)
# ────────────────────────────────────────────────────────────────
CONFIG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "config",
    "patterns",
)

_RULES_CACHE: list[dict[str, Any]] | None = None
_RULES_CONFIG_CACHE: dict[str, Any] | None = None
_RULES_MTIME: float = 0.0

import glob
import re

def _translate_cel_to_python(cel_expr: str) -> str:
    """Convert a CEL expression like 'features.metrics.time_ratio <= 0.75' to 'time_ratio <= 0.75'"""
    expr = cel_expr.replace("&&", "and").replace("||", "or")
    # Convert CEL negation `!` to Python `not `, avoiding `!=`
    expr = re.sub(r'!(?!=)', 'not ', expr)
    # Remove standard CEL prefixes and nested structures (e.g. features.rr.by_entry.entry_b -> entry_b)
    expr = re.sub(r"features\.(?:\w+\.)*(\w+)", r"\1", expr)
    expr = re.sub(r"context\.(?:\w+\.)*(\w+)", r"\1", expr)
    return expr

def _load_yaml() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    global _RULES_CACHE, _RULES_CONFIG_CACHE, _RULES_MTIME
    try:
        # Check mtime of the directory
        mtime = os.path.getmtime(CONFIG_DIR) if os.path.exists(CONFIG_DIR) else 0
        if _RULES_CACHE is None or mtime > _RULES_MTIME:
            patterns = []
            yaml_files = glob.glob(os.path.join(CONFIG_DIR, "*.yaml"))
            for file_path in yaml_files:
                if os.path.basename(file_path).startswith("_"):
                    continue
                with open(file_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                
                # Transform the complex schema into the flat schema expected by the classifier
                if "pattern" not in data:
                    continue
                
                cat = data["pattern"].get("key", "unknown")
                name_en = data["pattern"].get("names", {}).get("en", cat)
                name_fa = data["pattern"].get("names", {}).get("fa", name_en)
                
                # Extract rules from structure, ratios, completion, quality
                flat_rules = []
                for group, rule_list in data.get("rules", {}).items():
                    for r in rule_list:
                        cel = r.get("expr_cel", "")
                        if not cel:
                            continue
                        flat_rules.append({
                            "rule_id": r.get("id", "rule"),
                            "group": group,
                            "description": r.get("title_fa", r.get("title_en", "")),
                            "condition": _translate_cel_to_python(cel),
                            "var_left": cel,  # Store original CEL for reference
                            "operator": "expr_cel",
                            "var_right": "",
                        })
                # Extract ratios and thresholds from numbers block
                numbers = data.get("numbers", {})
                ratios = numbers.get("ratios", [])
                thresholds = numbers.get("thresholds", [])
                
                # Since flag.yaml is direction-agnostic, we duplicate it for bullish and bearish
                # so the classifier can match it against both.
                for direction in ["bullish", "bearish"]:
                    patterns.append({
                        "id": f"{cat}_{direction}",
                        "name_en": name_en,
                        "name_fa": f"{name_fa} ({'صعودی' if direction == 'bullish' else 'نزولی'})",
                        "category": cat,
                        "direction": direction,
                        "rules": flat_rules,
                        "ratios": ratios,
                        "thresholds": thresholds,
                    })

            _RULES_CACHE = patterns
            
            # Detector config is still loaded from data/pattern_rules.yaml if exists
            _RULES_CONFIG_CACHE = {}
            if os.path.exists(RULES_FILE):
                with open(RULES_FILE, encoding="utf-8") as f:
                    legacy_data = yaml.safe_load(f) or {}
                _RULES_CONFIG_CACHE = legacy_data.get("detector_config", {})
                
            _RULES_MTIME = mtime
    except Exception as exc:
        logger.error("Error loading pattern rules from config/patterns: %s", exc)
    return _RULES_CACHE or [], _RULES_CONFIG_CACHE or {}

def get_pattern_rules() -> list[dict[str, Any]]:
    """Return the pattern definitions from config/patterns/*.yaml (cached)."""
    rules, _ = _load_yaml()
    if not rules:
        logger.error("No pattern rules loaded from %s", CONFIG_DIR)
    return rules


def get_detector_config() -> dict[str, Any]:
    """Merged detector configuration: built-in defaults overridden by YAML."""
    _, yaml_cfg = _load_yaml()
    return {**DEFAULT_DETECTOR_CONFIG, **yaml_cfg}


def invalidate_rules_cache() -> None:
    """Force a reload of pattern rules on the next access (e.g. after a POST update)."""
    global _RULES_CACHE, _RULES_CONFIG_CACHE, _RULES_MTIME
    _RULES_CACHE = None
    _RULES_CONFIG_CACHE = None
    _RULES_MTIME = 0.0


def resolve_impulse_min_pct(config: dict[str, Any], asset_class: str | None = None) -> float:
    """Resolve the minimum impulse percentage for a given asset class."""
    by_class = config.get("impulse_min_pct_by_class") or {}
    if asset_class and asset_class in by_class:
        return float(by_class[asset_class])
    return float(config.get("impulse_min_pct_default", 0.018))


# ────────────────────────────────────────────────────────────────
# Rule evaluation & classification
# ────────────────────────────────────────────────────────────────
@dataclass
class RuleEvaluation:
    """Real evaluation result of a single YAML rule."""

    rule_id: str
    description: str
    condition: str
    passed: bool
    value: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": self.description or self.rule_id,
            "condition": self.condition,
            "passed": self.passed,
            "value": self.value,
        }


class RuleEngine:
    """Evaluates YAML pattern definitions against candidate features."""

    def evaluate_rule(
        self,
        rule: dict[str, Any],
        features: dict[str, Any],
    ) -> RuleEvaluation:
        """Evaluate one rule with REAL pass/fail and value diagnostics."""
        rule_id = str(rule.get("rule_id", "unknown"))
        description = str(rule.get("description", ""))
        condition = str(rule.get("condition", "")).strip()

        try:
            passed = evaluate_expression(condition, features)
            error: str | None = None
        except RuleConditionError as exc:
            passed = False
            error = str(exc)
            logger.warning("Rule '%s' condition failed to evaluate: %s", rule_id, exc)

        value = self._diagnostic_value(rule, condition, features)
        if error:
            value = f"ERROR: {error}"
        return RuleEvaluation(
            rule_id=rule_id,
            description=description,
            condition=condition,
            passed=passed,
            value=value,
        )

    @staticmethod
    def _diagnostic_value(
        rule: dict[str, Any],
        condition: str,
        features: dict[str, Any],
    ) -> str:
        """Format a human-readable 'left vs right' value for the UI."""
        left_expr = str(rule.get("var_left", "")).strip()
        right_expr = str(rule.get("var_right", "")).strip()
        targets = [e for e in (left_expr, right_expr) if e] or [condition]
        parts: list[str] = []
        for expr in targets:
            num = _eval_numeric(expr, features)
            parts.append(_format_number(num) if num is not None else "?")
        return " vs ".join(parts) if len(parts) > 1 else parts[0]

    def evaluate_pattern(
        self,
        pattern_def: dict[str, Any],
        features: dict[str, Any],
    ) -> list[RuleEvaluation] | None:
        """
        Evaluate all rules of a pattern definition (fail-fast).

        Returns:
            Full list of RuleEvaluation (all passed) on match, else None.
        """
        evaluations: list[RuleEvaluation] = []
        for rule in pattern_def.get("rules", []) or []:
            evaluation = self.evaluate_rule(rule, features)
            if not evaluation.passed:
                return None
            evaluations.append(evaluation)
        return evaluations

    def classify(
        self,
        features: dict[str, Any],
        direction: str,
    ) -> tuple[dict[str, Any] | None, list[RuleEvaluation]]:
        """
        Classify a candidate wave cycle via YAML rules.

        The first pattern definition (for the given direction) whose rules
        all pass is the detected pattern. Candidates matching no definition
        are discarded (no fake default labeling).
        """
        for pattern_def in get_pattern_rules():
            if pattern_def.get("direction") != direction:
                continue
            evaluations = self.evaluate_pattern(pattern_def, features)
            if evaluations is not None:
                return pattern_def, evaluations
        return None, []
