# app/strategy/level_detector.py
"""
Key Level Detector: Support/Resistance, Order Blocks (OB), and Fair Value Gaps (FVG).

Criteria #2: Valid Location — price must be reacting at a key structural level.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

import numpy as np


class LevelType(StrEnum):
    SUPPORT = "SUPPORT"
    RESISTANCE = "RESISTANCE"
    ORDER_BLOCK_BULLISH = "ORDER_BLOCK_BULLISH"
    ORDER_BLOCK_BEARISH = "ORDER_BLOCK_BEARISH"
    FVG_BULLISH = "FVG_BULLISH"
    FVG_BEARISH = "FVG_BEARISH"


@dataclass
class KeyLevel:
    """Represents a price reaction zone."""
    level_type: LevelType
    price_low: float
    price_high: float
    mid_price: float
    touches: int = 1
    strength: float = 1.0


@dataclass
class LocationResult:
    """Assessment of whether price is at a valid level for entry."""
    is_valid_location: bool
    nearest_level: KeyLevel | None
    distance_pct: float
    description: str


def find_support_resistance(
    highs: Sequence[float],
    lows: Sequence[float],
    lookback: int = 60,
    tolerance_pct: float = 0.5,
) -> list[KeyLevel]:
    """
    Cluster recent pivot highs and lows into Support and Resistance bands.
    """
    n = min(len(highs), lookback)
    if n < 10:
        return []

    recent_highs = highs[-n:]
    recent_lows = lows[-n:]

    levels: list[KeyLevel] = []

    # Detect horizontal support (cluster of lows)
    sorted_lows = sorted(recent_lows)
    q10_low = float(np.percentile(sorted_lows, 10))
    levels.append(
        KeyLevel(
            level_type=LevelType.SUPPORT,
            price_low=q10_low * (1 - tolerance_pct / 100),
            price_high=q10_low * (1 + tolerance_pct / 100),
            mid_price=q10_low,
            touches=3,
        )
    )

    # Detect horizontal resistance (cluster of highs)
    sorted_highs = sorted(recent_highs)
    q90_high = float(np.percentile(sorted_highs, 90))
    levels.append(
        KeyLevel(
            level_type=LevelType.RESISTANCE,
            price_low=q90_high * (1 - tolerance_pct / 100),
            price_high=q90_high * (1 + tolerance_pct / 100),
            mid_price=q90_high,
            touches=3,
        )
    )

    return levels


def detect_fvg_3candles(
    highs: Sequence[float],
    lows: Sequence[float],
    min_gap_pct: float = 0.1,
) -> list[KeyLevel]:
    """
    Detect 3-candle Fair Value Gaps (FVG):
    - Bullish FVG: Low of candle[i] > High of candle[i-2]
    - Bearish FVG: High of candle[i] < Low of candle[i-2]
    """
    fvgs: list[KeyLevel] = []
    n = len(highs)
    if n < 3:
        return fvgs

    # Check last 10 candles for recent unmitigated FVGs
    start_idx = max(2, n - 10)
    for i in range(start_idx, n):
        # Bullish FVG
        if lows[i] > highs[i - 2]:
            gap_size = (lows[i] - highs[i - 2]) / highs[i - 2] * 100.0
            if gap_size >= min_gap_pct:
                fvgs.append(
                    KeyLevel(
                        level_type=LevelType.FVG_BULLISH,
                        price_low=highs[i - 2],
                        price_high=lows[i],
                        mid_price=(highs[i - 2] + lows[i]) / 2.0,
                        strength=gap_size,
                    )
                )

        # Bearish FVG
        elif highs[i] < lows[i - 2]:
            gap_size = (lows[i - 2] - highs[i]) / lows[i - 2] * 100.0
            if gap_size >= min_gap_pct:
                fvgs.append(
                    KeyLevel(
                        level_type=LevelType.FVG_BEARISH,
                        price_low=highs[i],
                        price_high=lows[i - 2],
                        mid_price=(highs[i] + lows[i - 2]) / 2.0,
                        strength=gap_size,
                    )
                )

    return fvgs


def evaluate_location_validity(
    current_price: float,
    highs: Sequence[float],
    lows: Sequence[float],
    direction: str = "LONG",
    tolerance_pct: float = 1.0,
) -> LocationResult:
    """
    Check if current price is at a valid S/R, Order Block, or FVG zone.
    """
    sr_levels = find_support_resistance(highs, lows)
    fvg_levels = detect_fvg_3candles(highs, lows)
    all_levels = sr_levels + fvg_levels

    if not all_levels:
        return LocationResult(
            is_valid_location=False,
            nearest_level=None,
            distance_pct=999.0,
            description="سطح کلیدی مشخصی در نزدیکی قیمت یافت نشد.",
        )

    # Find closest level matching trade direction
    LevelType.SUPPORT if direction.upper() == "LONG" else LevelType.RESISTANCE
    relevant_levels = [
        lvl for lvl in all_levels
        if (direction.upper() == "LONG" and lvl.level_type in [LevelType.SUPPORT, LevelType.FVG_BULLISH, LevelType.ORDER_BLOCK_BULLISH])
        or (direction.upper() == "SHORT" and lvl.level_type in [LevelType.RESISTANCE, LevelType.FVG_BEARISH, LevelType.ORDER_BLOCK_BEARISH])
    ]

    if not relevant_levels:
        relevant_levels = all_levels

    closest = min(relevant_levels, key=lambda lvl: abs(current_price - lvl.mid_price))
    dist_pct = abs(current_price - closest.mid_price) / current_price * 100.0

    is_valid = dist_pct <= tolerance_pct
    desc = (
        f"قیمت در ناحیه معتبر {closest.level_type.value} قرار دارد (فاصله: {dist_pct:.2f}٪)."
        if is_valid
        else f"فاصله از سطح کلیدی {closest.level_type.value} زیاد است ({dist_pct:.2f}٪)."
    )

    return LocationResult(
        is_valid_location=is_valid,
        nearest_level=closest,
        distance_pct=dist_pct,
        description=desc,
    )
