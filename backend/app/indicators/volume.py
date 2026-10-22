# app/indicators/volume.py
"""
Volume Indicators.

Calculates Moving Average of volume and relative volume ratio.
Used for Criteria #6: Volume > MA(10).
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def calculate_volume_ma(
    volumes: Sequence[float],
    period: int = 10,
) -> list[float]:
    """
    Calculate Simple Moving Average (SMA) of volume.

    Returns a list of same length, with NaN for warmup bars.
    """
    n = len(volumes)
    if n < period:
        return [float("nan")] * n

    vol_arr = np.asarray(volumes, dtype=np.float64)
    ma_values: list[float] = [float("nan")] * (period - 1)

    # Rolling window mean
    for i in range(period - 1, n):
        window = vol_arr[i - period + 1 : i + 1]
        ma_values.append(float(np.mean(window)))

    return ma_values


def check_volume_confirmation(
    volumes: Sequence[float],
    period: int = 10,
    min_ratio: float = 1.0,
) -> tuple[bool, float, float]:
    """
    Check if latest closed candle volume exceeds its MA(period) by min_ratio.

    Returns:
        (is_confirmed, current_volume, volume_ma)
    """
    if len(volumes) < period:
        return False, 0.0, 0.0

    current_vol = float(volumes[-1])
    # Compute MA over the previous 'period' bars up to current
    vol_ma_list = calculate_volume_ma(volumes, period)
    current_ma = vol_ma_list[-1]

    if np.isnan(current_ma) or current_ma <= 0.0:
        return False, current_vol, 0.0

    ratio = current_vol / current_ma
    is_confirmed = ratio >= min_ratio
    return is_confirmed, current_vol, current_ma
