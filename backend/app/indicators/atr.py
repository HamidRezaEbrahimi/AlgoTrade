# app/indicators/atr.py
"""
Average True Range (ATR) Indicator.

Stateless mathematical calculation of market volatility.
Used for Trailing Stop placement (1.2 × ATR) and stop validation.
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def calculate_tr(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
) -> list[float]:
    """Calculate True Range (TR) for each candle."""
    n = len(highs)
    if n == 0:
        return []

    tr_values: list[float] = [highs[0] - lows[0]]
    for i in range(1, n):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        tr_values.append(max(hl, hc, lc))

    return tr_values


def calculate_atr(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    period: int = 14,
) -> list[float]:
    """
    Calculate ATR using Wilder's smoothing.

    Returns a list of same length, with NaN for initial warmup bars.
    """
    n = len(highs)
    if n < period:
        return [float("nan")] * n

    tr = calculate_tr(highs, lows, closes)
    atr_values = [float("nan")] * n

    # Initial ATR is simple average of first 'period' TR values
    atr = float(np.mean(tr[:period]))
    atr_values[period - 1] = atr

    # Wilder's smoothing for subsequent periods
    for i in range(period, n):
        atr = (atr * (period - 1) + tr[i]) / period
        atr_values[i] = atr

    return atr_values


def get_latest_atr(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    period: int = 14,
) -> float:
    """Convenience helper to get only the most recent ATR value."""
    atr_list = calculate_atr(highs, lows, closes, period)
    if not atr_list:
        return float("nan")
    return atr_list[-1]
