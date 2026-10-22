# app/strategy/__init__.py
"""Strategy Engine package — Pure signal calculations on closed candles."""

from app.strategy.grid_manager import (
    calculate_30day_sr_range,
    generate_symbol_grid,
    get_grid_allocated_size,
)
from app.strategy.level_detector import (
    KeyLevel,
    LevelType,
    detect_fvg_3candles,
    evaluate_location_validity,
    find_support_resistance,
)
from app.strategy.momentum_filter import (
    MomentumResult,
    evaluate_15m_momentum,
)
from app.strategy.pattern_detector import (
    PatternResult,
    PatternType,
    detect_1h_patterns,
)
from app.strategy.signal_scorer import (
    REASONS_FA,
    MultiTimeframeCandles,
    evaluate_signal,
)
from app.strategy.structure_analyzer import (
    StructureResult,
    TrendDirection,
    analyze_4h_structure,
    find_swing_points,
)

__all__ = [
    "analyze_4h_structure",
    "TrendDirection",
    "StructureResult",
    "find_swing_points",
    "detect_1h_patterns",
    "PatternType",
    "PatternResult",
    "evaluate_15m_momentum",
    "MomentumResult",
    "evaluate_location_validity",
    "find_support_resistance",
    "detect_fvg_3candles",
    "KeyLevel",
    "LevelType",
    "evaluate_signal",
    "MultiTimeframeCandles",
    "REASONS_FA",
    "generate_symbol_grid",
    "get_grid_allocated_size",
    "calculate_30day_sr_range",
]
