# app/indicators/rsi.py
"""
Relative Strength Index (RSI) Indicator.

Stateless mathematical function using Wilder's smoothing method.
Standard period = 14.
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def calculate_rsi(
    prices: Sequence[float],
    period: int = 14,
) -> list[float]:
    """
    Calculate RSI values for a sequence of closing prices.

    Uses Wilder's Exponential Smoothing (standard RSI definition).
    Returns a list of same length, with NaN for initial warmup periods.
    """
    if len(prices) < period + 1:
        return [float("nan")] * len(prices)

    prices_arr = np.asarray(prices, dtype=np.float64)
    deltas = np.diff(prices_arr)

    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    rsi_values = [float("nan")] * len(prices)

    # Initial average gain/loss (Simple Average of first 'period' deltas)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    if avg_loss == 0.0:
        rsi_values[period] = 100.0 if avg_gain > 0.0 else 50.0
    else:
        rs = avg_gain / avg_loss
        rsi_values[period] = float(100.0 - (100.0 / (1.0 + rs)))

    # Wilder's smoothing for subsequent periods
    for i in range(period + 1, len(prices)):
        gain = gains[i - 1]
        loss = losses[i - 1]

        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

        if avg_loss == 0.0:
            rsi_values[i] = 100.0 if avg_gain > 0.0 else 50.0
        else:
            rs = avg_gain / avg_loss
            rsi_values[i] = float(100.0 - (100.0 / (1.0 + rs)))

    return rsi_values


def get_latest_rsi(prices: Sequence[float], period: int = 14) -> float:
    """Convenience helper to get only the most recent RSI value."""
    rsi_list = calculate_rsi(prices, period)
    if not rsi_list:
        return float("nan")
    return rsi_list[-1]
