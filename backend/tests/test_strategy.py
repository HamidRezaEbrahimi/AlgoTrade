# tests/test_strategy.py
"""
Unit tests for Strategy Engine (4H Structure, 1H Patterns, Grid, 8-Criteria Scoring).
"""

from app.strategy.grid_manager import generate_symbol_grid
from app.strategy.pattern_detector import (
    PatternType,
    detect_1h_patterns,
    detect_bullish_engulfing,
)
from app.strategy.structure_analyzer import TrendDirection, analyze_4h_structure


def test_structure_analyzer_bullish():
    """Verify Higher Highs & Higher Lows detected as BULLISH."""
    highs = [100.0, 105.0, 102.0, 110.0, 108.0, 115.0, 112.0, 120.0]
    lows = [90.0, 95.0, 93.0, 100.0, 98.0, 105.0, 103.0, 110.0]
    closes = [98.0, 104.0, 100.0, 109.0, 106.0, 114.0, 111.0, 119.0]

    result = analyze_4h_structure(highs, lows, closes, lookback=1)
    assert result.direction == TrendDirection.BULLISH


def test_pattern_detector_bullish_engulfing():
    """Verify Bullish Engulfing pattern detection."""
    # Previous: Open=100, Close=92 (bearish body = 8)
    # Current: Open=91 (below prev close), Close=105 (above prev open 100) -> Bullish Engulfing
    opens = [100.0, 91.0]
    highs = [102.0, 106.0]
    lows = [90.0, 90.0]
    closes = [92.0, 105.0]

    assert detect_bullish_engulfing(opens, highs, lows, closes) is True
    res = detect_1h_patterns(opens, highs, lows, closes)
    assert res.pattern_type == PatternType.BULLISH_ENGULFING
    assert res.is_bullish is True


def test_grid_manager_disabling_under_4pct():
    """Verify grid is automatically disabled if 30-day S/R range < 4%."""
    # Resistance = 102, Support = 100 -> Range = 2% (< 4%)
    highs = [101.0, 102.0, 101.5]
    lows = [100.0, 100.5, 100.2]

    grid = generate_symbol_grid("BTCUSDT", highs, lows, num_levels=25, min_range_pct=4.0)
    assert grid.is_enabled is False
    assert len(grid.levels) == 0

    # Resistance = 110, Support = 100 -> Range = 10% (>= 4%)
    highs_wide = [105.0, 110.0, 108.0]
    lows_wide = [100.0, 102.0, 101.0]

    grid_wide = generate_symbol_grid("BTCUSDT", highs_wide, lows_wide, num_levels=25, min_range_pct=4.0)
    assert grid_wide.is_enabled is True
    assert len(grid_wide.levels) == 25
