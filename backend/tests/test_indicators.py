# tests/test_indicators.py
"""
Unit tests for Mathematical Indicators (RSI, ATR, Volume, R:R).
"""
import numpy as np

from app.indicators.atr import calculate_atr
from app.indicators.risk_reward import (
    calculate_risk_reward,
    calculate_target_by_rr,
    validate_risk_reward,
)
from app.indicators.rsi import calculate_rsi, get_latest_rsi
from app.indicators.volume import check_volume_confirmation


def test_rsi_calculation(sample_prices):
    """Verify RSI calculation outputs numbers in valid 0-100 bounds."""
    rsi_list = calculate_rsi(sample_prices, period=14)
    assert len(rsi_list) == len(sample_prices)
    # Warmup values should be NaN
    assert np.isnan(rsi_list[0])
    assert np.isnan(rsi_list[13])
    # 15th element onward must be valid number between 0 and 100
    latest = get_latest_rsi(sample_prices, period=14)
    assert 0.0 <= latest <= 100.0
    # Uptrend should have RSI > 50
    assert latest > 50.0


def test_atr_calculation():
    """Verify True Range and ATR calculations."""
    highs = [105.0, 107.0, 106.0, 108.0, 110.0] * 4
    lows = [95.0, 97.0, 96.0, 98.0, 100.0] * 4
    closes = [100.0, 102.0, 101.0, 104.0, 105.0] * 4

    atr_list = calculate_atr(highs, lows, closes, period=14)
    assert len(atr_list) == len(highs)
    latest_atr = atr_list[-1]
    assert latest_atr > 0.0
    assert not np.isnan(latest_atr)


def test_volume_confirmation():
    """Verify Volume > MA(10) confirmation."""
    volumes = [100.0] * 15
    volumes[-1] = 200.0  # Spike

    is_confirmed, curr_vol, vol_ma = check_volume_confirmation(volumes, period=10, min_ratio=1.2)
    assert is_confirmed is True
    assert curr_vol == 200.0
    assert vol_ma == 110.0


def test_risk_reward_calculations():
    """Verify R:R math, validation, and price target projections."""
    # Long trade: Entry=100, Stop=90 (Risk=10), Target=115 (Reward=15) -> RR=1.5
    rr = calculate_risk_reward(100.0, 90.0, 115.0, direction="LONG")
    assert rr == 1.5

    is_valid, _ = validate_risk_reward(100.0, 90.0, 115.0, direction="LONG", min_rr=1.5)
    assert is_valid is True

    # Target calculation
    target_15 = calculate_target_by_rr(100.0, 90.0, target_rr=1.5, direction="LONG")
    assert target_15 == 115.0

    target_25 = calculate_target_by_rr(100.0, 90.0, target_rr=2.5, direction="LONG")
    assert target_25 == 125.0
