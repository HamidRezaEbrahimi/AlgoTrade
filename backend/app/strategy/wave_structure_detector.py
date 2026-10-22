# app/strategy/wave_structure_detector.py
"""
Backward-compatibility shim.

The implementation moved to the modular package ``app/strategy/patterns/``:
- rule_engine.py      → safe AST rule evaluation + YAML config
- wave_points.py      → pure P0-P5 wave-cycle geometry
- wave_classifier.py  → orchestration, classification, de-duplication

All public names are re-exported unchanged so existing imports
(e.g. app/strategy/pattern_detector.py) keep working.
"""
from __future__ import annotations

from app.strategy.patterns.rule_engine import (  # noqa: F401
    DEFAULT_DETECTOR_CONFIG,
    PATTERN_COLORS,
    RuleConditionError,
    RuleEngine,
    RuleEvaluation,
    evaluate_expression,
    get_detector_config,
    get_pattern_rules,
    resolve_impulse_min_pct,
)
from app.strategy.patterns.wave_classifier import (  # noqa: F401
    scan_canonical_wave_patterns,
)
from app.strategy.patterns.wave_points import (  # noqa: F401
    build_features,
    calc_atr,
    extract_candidate_wave_cycles,
    extract_wave_cycle,
    is_clean_impulse,
)


def safe_eval(expr: str, local_vars: dict) -> bool:
    """
    Backward-compatible wrapper around the safe AST evaluator.

    Legacy contract preserved: returns False on any evaluation error
    (the new engine logs the underlying cause loudly via RuleEngine).
    """
    try:
        from app.strategy.patterns.rule_engine import evaluate_expression

        return evaluate_expression(expr, local_vars)
    except Exception:
        return False


__all__ = [
    "scan_canonical_wave_patterns",
    "get_pattern_rules",
    "get_detector_config",
    "resolve_impulse_min_pct",
    "evaluate_expression",
    "safe_eval",
    "RuleEngine",
    "RuleEvaluation",
    "RuleConditionError",
    "DEFAULT_DETECTOR_CONFIG",
    "PATTERN_COLORS",
    "extract_candidate_wave_cycles",
    "extract_wave_cycle",
    "build_features",
]
