# app/strategy/patterns/__init__.py
"""
Chart & Wave Pattern Detection Package (v2).

Pipeline:
1. wave_points.py: pure geometry (ATR, swings, clean impulse, P0-P5 extraction).
2. rule_engine.py: safe AST-based evaluation of YAML pattern rules.
3. wave_classifier.py: orchestration, classification, de-duplication, markers.
4. trade_zones.py: per-pattern Entry A/B, Stop Loss, TP1, TP2 calculations.
5. context_filters.py: toggleable context filters (CHoCH, Volume, RSI, Trend).
"""
from app.strategy.patterns.context_filters import (
    ContextTag,
    FilterConfig,
    apply_context_filters,
)
from app.strategy.patterns.rule_engine import (
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
from app.strategy.patterns.trade_zones import (
    PatternTradeZones,
    TradeZone,
    calculate_trade_zones,
)
from app.strategy.patterns.wave_classifier import scan_canonical_wave_patterns
from app.strategy.patterns.wave_points import (
    build_features,
    calc_atr,
    extract_candidate_wave_cycles,
    extract_wave_cycle,
    is_clean_impulse,
)

__all__ = [
    "RuleEngine",
    "RuleEvaluation",
    "RuleConditionError",
    "evaluate_expression",
    "get_pattern_rules",
    "get_detector_config",
    "resolve_impulse_min_pct",
    "PATTERN_COLORS",
    "DEFAULT_DETECTOR_CONFIG",
    "calc_atr",
    "is_clean_impulse",
    "extract_candidate_wave_cycles",
    "extract_wave_cycle",
    "build_features",
    "scan_canonical_wave_patterns",
    # New v2 exports
    "TradeZone",
    "PatternTradeZones",
    "calculate_trade_zones",
    "FilterConfig",
    "ContextTag",
    "apply_context_filters",
]
