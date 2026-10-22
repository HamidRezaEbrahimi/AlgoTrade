# app/strategy/structure_analyzer.py
"""
Market Structure Analyzer (4H Timeframe).

Detects:
- Swing Highs and Swing Lows (pivot points)
- Trend direction: Bullish (HH + HL) vs Bearish (LH + LL) vs Neutral
- Break of Structure (BOS)
- Change of Character (CHoCH)
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum


class TrendDirection(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


@dataclass
class SwingPoint:
    """Represents a pivot high or pivot low."""
    index: int
    price: float
    is_high: bool  # True for swing high, False for swing low


@dataclass
class StructureResult:
    """Output of 4H market structure analysis."""
    direction: TrendDirection
    has_bos: bool
    has_choch: bool
    last_swing_high: float | None
    last_swing_low: float | None
    description: str


def find_swing_points(
    highs: Sequence[float],
    lows: Sequence[float],
    lookback: int = 5,
) -> list[SwingPoint]:
    """
    Find local swing highs and swing lows using a symmetric window.
    """
    n = len(highs)
    swings: list[SwingPoint] = []
    if n < lookback * 2 + 1:
        return swings

    for i in range(lookback, n - lookback):
        current_high = highs[i]
        current_low = lows[i]

        # Check Swing High
        is_swing_high = all(
            current_high >= highs[i - j] and current_high >= highs[i + j]
            for j in range(1, lookback + 1)
        )
        if is_swing_high:
            swings.append(SwingPoint(index=i, price=current_high, is_high=True))

        # Check Swing Low
        is_swing_low = all(
            current_low <= lows[i - j] and current_low <= lows[i + j]
            for j in range(1, lookback + 1)
        )
        if is_swing_low:
            swings.append(SwingPoint(index=i, price=current_low, is_high=False))

    return swings


def analyze_4h_structure(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    lookback: int = 5,
) -> StructureResult:
    """
    Analyze 4H market structure on closed candles.

    Determines if market is making HH/HL (Bullish) or LH/LL (Bearish),
    and whether a BOS or CHoCH just occurred.
    """
    swings = find_swing_points(highs, lows, lookback)
    high_swings = [s for s in swings if s.is_high]
    low_swings = [s for s in swings if not s.is_high]

    last_high = high_swings[-1].price if high_swings else None
    last_low = low_swings[-1].price if low_swings else None

    if len(high_swings) < 2 or len(low_swings) < 2 or len(closes) == 0:
        return StructureResult(
            direction=TrendDirection.NEUTRAL,
            has_bos=False,
            has_choch=False,
            last_swing_high=last_high,
            last_swing_low=last_low,
            description="داده‌های نوسانی برای تحلیل ساختار ۴ ساعته ناکافی است.",
        )

    current_close = closes[-1]
    prev_high = high_swings[-2].price
    curr_high = high_swings[-1].price
    prev_low = low_swings[-2].price
    curr_low = low_swings[-1].price

    is_hh = curr_high > prev_high
    is_hl = curr_low > prev_low
    is_lh = curr_high < prev_high
    is_ll = curr_low < prev_low

    # Check BOS (Break of structure in trend direction)
    has_bos = (is_hh and current_close > curr_high) or (is_ll and current_close < curr_low)

    # Check CHoCH (Change of Character: breaking counter-trend swing)
    has_choch = False
    if is_lh and is_ll and current_close > curr_high:
        # Was bearish, but broke above last swing high
        has_choch = True
        direction = TrendDirection.BULLISH
        desc = "تغییر کاراکتر صعودی (CHoCH): شکست سقف قبلی در روند نزولی."
    elif is_hh and is_hl and current_close < curr_low:
        # Was bullish, but broke below last swing low
        has_choch = True
        direction = TrendDirection.BEARISH
        desc = "تغییر کاراکتر نزولی (CHoCH): شکست کف قبلی در روند صعودی."
    elif is_hh and is_hl:
        direction = TrendDirection.BULLISH
        desc = "ساختار صعودی معتبر (Higher Highs & Higher Lows)."
    elif is_lh and is_ll:
        direction = TrendDirection.BEARISH
        desc = "ساختار نزولی معتبر (Lower Highs & Lower Lows)."
    else:
        direction = TrendDirection.NEUTRAL
        desc = "ساختار خنثی / بدون روند قطعی."

    return StructureResult(
        direction=direction,
        has_bos=has_bos,
        has_choch=has_choch,
        last_swing_high=last_high,
        last_swing_low=last_low,
        description=desc,
    )
