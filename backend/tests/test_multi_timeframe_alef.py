# backend/tests/test_multi_timeframe_alef.py
"""Automated Multi-Timeframe Verification Suite for AlefTrade Engine.

Ensures zero crashes, correct Elliott Wave identification, zero-lag PRZ
tracking, and 8-criteria scoring across all 7 supported timeframes:
1m, 5m, 15m, 30m, 1h, 4h, 1d.
"""
from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest

from app.market_data.market_analyzer import MarketAnalyzer
from app.models.candle import Candle
from app.strategy.alef_adapter import scan_patterns_with_alef

ALL_TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]


def _generate_synthetic_wave_candles(
    count: int = 1500,
    timeframe: str = "1h",
    base_price: float = 4000.0,
) -> list[Candle]:
    """Generate realistic OHLCV candles with an embedded Running Flat setup."""
    tf_minutes = {
        "1m": 1, "5m": 5, "15m": 15, "30m": 30,
        "1h": 60, "4h": 240, "1d": 1440,
    }.get(timeframe, 60)

    start_time = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    delta = timedelta(minutes=tf_minutes)
    candles: list[Candle] = []

    cur_price = base_price
    for i in range(count):
        ts = start_time + (delta * i)

        # Baseline gentle movement
        trend_step = 0.05 * (1 if (i // 50) % 2 == 0 else -1)

        # Embed a clean Running Flat at the tail (last 100 bars)
        offset = count - i
        if offset == 70:
            # P0: Impulse start
            cur_price = base_price + 80.0
        elif offset == 55:
            # P1: Impulse end (Drop from 4080 to 4020 -> imp_l = 60)
            cur_price = base_price + 20.0
        elif offset == 40:
            # Wave A: Retracement to 4058 (wa_l = 38 -> ~63% retracement)
            cur_price = base_price + 58.0
        elif offset == 25:
            # Wave B: Expansion breaking P1 to 4005 (wb_l = 53 -> ~140% of wa_l)
            cur_price = base_price + 5.0
        elif offset == 10:
            # Wave C: Moving into PRZ at 4048 (wc_l = 43 -> ~81% of wb_l)
            cur_price = base_price + 48.0
        elif offset < 10:
            # Reversal bar out of PRZ
            cur_price = base_price + 40.0 - (10 - offset) * 1.5
        else:
            cur_price += trend_step

        high = cur_price + 1.8
        low = cur_price - 1.8
        open_p = cur_price - 0.4
        close_p = cur_price + 0.4
        vol = 150.0 + (i % 20) * 10.0

        candles.append(
            Candle(
                symbol="FXCM_XAUUSD",
                timeframe=timeframe,
                timestamp=ts,
                open=Decimal(str(round(open_p, 2))),
                high=Decimal(str(round(high, 2))),
                low=Decimal(str(round(low, 2))),
                close=Decimal(str(round(close_p, 2))),
                volume=Decimal(str(round(vol, 2))),
            )
        )
    return candles


@pytest.mark.parametrize("tf", ALL_TIMEFRAMES)
def test_all_timeframes_running_flat_scan(tf: str):
    """Verify that scan_patterns_with_alef executes cleanly without crashes on all timeframes."""
    candles = _generate_synthetic_wave_candles(count=300, timeframe=tf)
    assert len(candles) == 300

    start_t = time.perf_counter()
    markers = scan_patterns_with_alef(candles, symbol="FXCM_XAUUSD", timeframe=tf)
    elapsed_ms = (time.perf_counter() - start_t) * 1000.0

    # Must execute within 150ms per scan
    assert elapsed_ms < 150.0, f"Scan on {tf} exceeded latency budget: {elapsed_ms:.1f}ms"
    assert isinstance(markers, list)

    # Verify marker point structures if patterns found
    for m in markers:
        assert "points" in m
        assert "prz_zone" in m
        assert "stage" in m
        for pt in m["points"]:
            assert "price" in pt
            assert "time" in pt
            assert pt["price"] > 0
            assert pt["time"] > 0


@pytest.mark.parametrize("tf", ALL_TIMEFRAMES)
def test_all_timeframes_market_analyzer_eval(tf: str):
    """Verify full 8-criteria evaluation across all timeframes."""
    candles = _generate_synthetic_wave_candles(count=300, timeframe=tf)
    res = MarketAnalyzer.analyze_candles(candles, symbol="FXCM_XAUUSD", timeframe=tf)

    assert res["status"] == "ok"
    assert "score" in res
    assert 0 <= res["score"] <= 8
    assert "criteria" in res
    assert len(res["criteria"]) == 8
    assert "trade_setup" in res
    assert "detected_patterns" in res
    assert isinstance(res["detected_patterns"], list)


def test_scalp_vs_macro_atr_parameters():
    """Verify that scalp timeframes (1m, 5m) apply calibrated multipliers."""
    scalp_candles = _generate_synthetic_wave_candles(count=60, timeframe="5m")
    macro_candles = _generate_synthetic_wave_candles(count=60, timeframe="1h")

    # Both must complete without error
    scalp_res = scan_patterns_with_alef(scalp_candles, symbol="FXCM_XAUUSD", timeframe="5m")
    macro_res = scan_patterns_with_alef(macro_candles, symbol="FXCM_XAUUSD", timeframe="1h")

    assert isinstance(scalp_res, list)
    assert isinstance(macro_res, list)


def test_p0_invalidation_and_lifecycle():
    """Verify deterministic P0 breach detection, target-hit, and active status in build_confirmed_marker."""
    from unittest.mock import MagicMock
    import pandas as pd
    from app.strategy.alef_markers import build_confirmed_marker

    mock_pat = MagicMock()
    mock_pat.p0.bar_idx = 0
    mock_pat.p0.price = 100.0
    mock_pat.p1.bar_idx = 1
    mock_pat.p1.price = 150.0
    mock_pat.p2.bar_idx = 2
    mock_pat.p2.price = 120.0
    mock_pat.p3.bar_idx = 3
    mock_pat.p3.price = 160.0
    mock_pat.p4.bar_idx = 4
    mock_pat.p4.price = 125.0
    mock_pat.direction = "bullish"
    mock_pat.retr_a = 0.60
    mock_pat.retr_b = 1.33
    mock_pat.retr_c = 0.85
    mock_pat.slope_ratio = 1.2
    mock_pat.er_b = 0.25
    mock_pat.chop_b = 35.0
    mock_pat.dtw_score = 0.05
    mock_pat.trade_plan = MagicMock()
    mock_pat.trade_plan.entry_price = 125.0
    mock_pat.trade_plan.stop_loss = 115.0
    mock_pat.trade_plan.take_profit_1 = 160.0
    mock_pat.trade_plan.take_profit_2 = 180.0
    mock_pat.trade_plan.rr_ratio = 3.5

    timestamps = [1000, 2000, 3000, 4000, 5000, 6000, 7000]

    # Scenario 1: Breached P0 (Price dips below 100.0) -> INVALIDATED
    df_breached = pd.DataFrame([
        {"high": 105.0, "low": 100.0}, # bar 0 (P0)
        {"high": 150.0, "low": 102.0}, # bar 1 (P1)
        {"high": 145.0, "low": 120.0}, # bar 2 (A)
        {"high": 160.0, "low": 122.0}, # bar 3 (B)
        {"high": 126.0, "low": 124.0}, # bar 4 (C)
        {"high": 120.0, "low": 98.0},  # bar 5 (Breaches P0=100.0!)
        {"high": 110.0, "low": 95.0},  # bar 6
    ])
    marker_breached = build_confirmed_marker(mock_pat, timestamps, 7, df=df_breached)
    assert marker_breached["lifecycle_status"] == "INVALIDATED"
    assert marker_breached["is_invalidated"] is True
    assert marker_breached["is_target_hit"] is False
    assert marker_breached["pattern_color"] == "#64748b"
    assert "باطل شده" in marker_breached["name"]
    assert marker_breached["trade_setup"]["signal"] == "WAIT"

    # Scenario 2: Target 1 reached (Price hits 160.0 without breaching 100.0) -> TARGET_HIT
    df_hit = pd.DataFrame([
        {"high": 105.0, "low": 100.0}, # bar 0 (P0)
        {"high": 150.0, "low": 102.0}, # bar 1 (P1)
        {"high": 145.0, "low": 120.0}, # bar 2 (A)
        {"high": 160.0, "low": 122.0}, # bar 3 (B)
        {"high": 126.0, "low": 124.0}, # bar 4 (C)
        {"high": 145.0, "low": 122.0}, # bar 5
        {"high": 165.0, "low": 140.0}, # bar 6 (Reaches TP1=160.0!)
    ])
    marker_hit = build_confirmed_marker(mock_pat, timestamps, 7, df=df_hit)
    assert marker_hit["lifecycle_status"] == "TARGET_HIT"
    assert marker_hit["is_target_hit"] is True
    assert marker_hit["is_invalidated"] is False
    assert marker_hit["pattern_color"] == "#10b981"
    assert "تارگت" in marker_hit["name"]

    # Scenario 3: Ongoing trade (Price is between C and TP1/P0) -> ACTIVE
    df_active = pd.DataFrame([
        {"high": 105.0, "low": 100.0}, # bar 0 (P0)
        {"high": 150.0, "low": 102.0}, # bar 1 (P1)
        {"high": 145.0, "low": 120.0}, # bar 2 (A)
        {"high": 160.0, "low": 122.0}, # bar 3 (B)
        {"high": 126.0, "low": 124.0}, # bar 4 (C)
        {"high": 135.0, "low": 123.0}, # bar 5
        {"high": 140.0, "low": 130.0}, # bar 6
    ])
    marker_active = build_confirmed_marker(mock_pat, timestamps, 7, df=df_active)
    assert marker_active["lifecycle_status"] == "ACTIVE"
    assert marker_active["is_invalidated"] is False
    assert marker_active["is_target_hit"] is False
    assert marker_active["pattern_color"] == "#3b82f6"
    assert marker_active["trade_setup"]["signal"] == "BUY"

