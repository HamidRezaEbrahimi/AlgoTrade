# app/strategy/condition_evaluator.py
"""
CEL-like Condition Evaluator.

Evaluates simple expression strings against a features dictionary.
Inspired by Financial-Labeling-Tool's pattern_scenario_matcher but
optimized for trading strategy conditions.

Supported syntax:
  - Boolean paths:       "features.structure_valid"
  - Negation:            "!features.invalidated"
  - Comparisons:         "features.rr.entry_b >= 1.5"
  - String equality:     "context.direction == 'LONG'"
  - Nested dot paths:    "features.impulses.i2_slope_ratio >= 0.7"
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("algotrade.strategy.condition_evaluator")

# Pre-compiled regex for comparison operators
_COMPARISON_RE = re.compile(
    r"^(.+?)\s*(>=|<=|==|!=|>|<)\s*(.+)$"
)


class ConditionError(Exception):
    """Raised when a condition expression cannot be evaluated."""


def evaluate_conditions(
    conditions: dict[str, list[str]],
    features: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> bool:
    """
    Evaluate a conditions block with all/any/none lists.

    Args:
        conditions: Dict with optional keys 'all', 'any', 'none'.
        features: Nested dict of computed features.
        context: Optional context dict (direction, timeframe, etc.).

    Returns:
        True if all condition groups pass.
    """
    if context is None:
        context = {}

    all_conds = conditions.get("all", [])
    any_conds = conditions.get("any", [])
    none_conds = conditions.get("none", [])

    # ALL: every expression must be true
    if all_conds:
        for expr in all_conds:
            if not _evaluate_single(expr, features, context):
                return False

    # ANY: at least one must be true
    if any_conds and not any(_evaluate_single(e, features, context) for e in any_conds):
        return False

    # NONE: every expression must be false
    if none_conds:
        for expr in none_conds:
            if _evaluate_single(expr, features, context):
                return False

    return True


def evaluate_single_condition(
    expr: str,
    features: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> bool:
    """Evaluate a single CEL-like expression. Public API."""
    return _evaluate_single(expr, features, context or {})


def _evaluate_single(
    expr: str,
    features: dict[str, Any],
    context: dict[str, Any],
) -> bool:
    """Evaluate one CEL-like expression."""
    expr = expr.strip()
    if not expr:
        return True  # Empty expression is vacuously true

    # Handle negation
    negated = False
    if expr.startswith("!"):
        negated = True
        expr = expr[1:].strip()

    # Check for comparison operator
    match = _COMPARISON_RE.match(expr)
    if match:
        left_path = match.group(1).strip()
        operator = match.group(2)
        right_raw = match.group(3).strip()

        left_val = _resolve_path(left_path, features, context)
        right_val = _parse_literal(right_raw)

        result = _compare(left_val, operator, right_val)
        return (not result) if negated else result

    # No operator → boolean path check
    val = _resolve_path(expr, features, context)
    result = bool(val)
    return (not result) if negated else result


def _resolve_path(
    path: str,
    features: dict[str, Any],
    context: dict[str, Any],
) -> Any:
    """
    Resolve a dotted path to a value.

    "features.rr.entry_b" → features["rr"]["entry_b"]
    "context.direction"   → context["direction"]
    """
    parts = path.split(".")
    if not parts:
        return None

    root = parts[0]
    if root == "features":
        current: Any = features
        walk = parts[1:]
    elif root == "context":
        current = context
        walk = parts[1:]
    else:
        # Default to features namespace
        current = features
        walk = parts

    for segment in walk:
        if isinstance(current, dict):
            current = current.get(segment)
        else:
            return None
        if current is None:
            return None

    return current


def _parse_literal(raw: str) -> Any:
    """Parse a literal value from expression right-hand side."""
    raw = raw.strip()

    # Quoted string
    if (raw.startswith("'") and raw.endswith("'")) or (
        raw.startswith('"') and raw.endswith('"')
    ):
        return raw[1:-1]

    # Boolean
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False

    # Number
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        pass

    return raw


def _compare(left: Any, op: str, right: Any) -> bool:
    """Compare two values with the given operator."""
    if left is None:
        return False

    try:
        if _is_number(left) and _is_number(right):
            lf, rf = float(left), float(right)
            if op == ">=":
                return lf >= rf
            if op == "<=":
                return lf <= rf
            if op == ">":
                return lf > rf
            if op == "<":
                return lf < rf
            if op == "==":
                return abs(lf - rf) < 1e-9
            if op == "!=":
                return abs(lf - rf) >= 1e-9

        if op == "==":
            return left == right
        if op == "!=":
            return left != right
    except (ValueError, TypeError):
        return False

    return False


def _is_number(value: Any) -> bool:
    """Check if value is numeric (excluding booleans)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)
