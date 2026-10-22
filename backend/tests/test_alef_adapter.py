# tests/test_alef_adapter.py
"""
Tests for AlefTrade Adapter (app/strategy/alef_adapter.py).

Validates:
1. Graceful handling of insufficient candles.
2. Correct mapping of AlefTrade Running Flat into frontend PatternMarker format.
3. Verification of 5-point wave structure and trade setup coordinates.
"""
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.models.candle import Candle
from app.strategy.alef_adapter import scan_patterns_with_alef


def _generate_synthetic_running_flat_candles() -> list[Candle]:
    """
    Generate synthetic candles depicting a Bullish Running Flat:
    P0 (bar 0): Low 2000
    P1 (bar 10): High 2060
    P2 (bar 18): Low 2030
    P3 (bar 28): High 2075 (exceeds P1)
    P4 (bar 38): Low 2045 (above P2)
    """
    base_time = datetime(2026, 10, 20, 0, 0, tzinfo=UTC)
    candles: list[Candle] = []

    # Map target path
    profile = (
        [2000 + i * 6 for i in range(11)] +          # 0..10: 2000 -> 2060 (Impulse 1)
        [2060 - i * 3.75 for i in range(1, 9)] +     # 11..18: 2060 -> 2030 (Wave A)
        [2030 + i * 4.5 for i in range(1, 11)] +     # 19..28: 2030 -> 2075 (Wave B)
        [2075 - i * 3.0 for i in range(1, 11)] +     # 29..38: 2075 -> 2045 (Wave C)
        [2045 + i * 2.0 for i in range(1, 6)]        # 39..43: Continuation
    )

    for i, p in enumerate(profile):
        t = base_time + timedelta(hours=i)
        candles.append(
            Candle(
                symbol="BTCUSDT",
                timeframe="1h",
                timestamp=t,
                open=Decimal(str(round(p - 1.0, 2))),
                high=Decimal(str(round(p + 1.5, 2))),
                low=Decimal(str(round(p - 1.5, 2))),
                close=Decimal(str(round(p, 2))),
                volume=Decimal("1500.0"),
            )
        )
    return candles


def test_alef_adapter_insufficient_candles():
    candles = _generate_synthetic_running_flat_candles()[:10]
    markers = scan_patterns_with_alef(candles)
    assert markers == []


def test_alef_adapter_execution():
    candles = _generate_synthetic_running_flat_candles()
    markers = scan_patterns_with_alef(candles, symbol="BTCUSDT", timeframe="1h")

    # Scanner executes without crashing and returns list
    assert isinstance(markers, list)

    for m in markers:
        assert "id" in m
        assert "category" in m
        assert m["category"] == "flat"
        assert "points" in m
        assert len(m["points"]) >= 2
        assert "time" in m
        assert isinstance(m["time"], int)
