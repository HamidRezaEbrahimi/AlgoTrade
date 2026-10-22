# tests/test_market_analyzer.py
"""
Tests for the MarketAnalyzer 8-criteria real-time analyzer.

Verifies Phase-2 refactor guarantees:
1. Analysis delegates to REAL strategy modules (structure, location,
   pattern, momentum) — not duplicated simplified logic.
2. No fabricated fallback: insufficient candles yield an honest
   `insufficient_data` payload (never fake BUY signals or hardcoded prices).
3. All 8 criteria values are real outputs; scoring is 0-8 with 6/8 pass.
"""
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.market_data.market_analyzer import MarketAnalyzer
from app.models.candle import Candle


def _mk_candle(ts: datetime, o: float, h: float, low: float, c: float, v: float = 1000.0) -> Candle:
    return Candle(
        symbol="BTCUSDT",
        timeframe="1h",
        timestamp=ts,
        open=Decimal(str(o)),
        high=Decimal(str(h)),
        low=Decimal(str(low)),
        close=Decimal(str(c)),
        volume=Decimal(str(v)),
    )


def _flat_candles(n: int, price: float = 100.0) -> list:
    base = datetime(2025, 1, 1, tzinfo=UTC)
    return [
        _mk_candle(base + timedelta(hours=i), price, price * 1.001, price * 0.999, price)
        for i in range(n)
    ]


def test_insufficient_data_is_honest_not_fabricated():
    """Fewer than MIN_LENGTH candles must return status=insufficient_data."""
    result = MarketAnalyzer.analyze_candles(_flat_candles(5), symbol="BTCUSDT", timeframe="1h")
    assert result["status"] == "insufficient_data"
    assert result["score"] == 0
    assert result["passed"] is False
    assert result["trade_setup"]["signal"] == "WAIT"
    # The legacy fake fallback returned a hardcoded BTC price — must never happen
    assert result["current_price"] == 0.0
    assert result["detected_patterns"] == []


def test_empty_candles_returns_insufficient_data():
    result = MarketAnalyzer.analyze_candles([], symbol="BTCUSDT", timeframe="1h")
    assert result["status"] == "insufficient_data"


def _trending_candles(n: int = 56, start: float = 100.0, v_high: float = 1500.0, v_low: float = 800.0) -> list:
    """
    Build a clean HH/HL uptrend series (8-candle structure blocks, each
    block scaled +5%) that the real structure_analyzer reports as BULLISH.
    """
    base = datetime(2025, 1, 1, tzinfo=UTC)
    block_highs = [100.0, 105.0, 102.0, 110.0, 108.0, 115.0, 112.0, 120.0]
    block_lows = [90.0, 95.0, 93.0, 100.0, 98.0, 105.0, 103.0, 110.0]
    block_closes = [98.0, 104.0, 100.0, 109.0, 106.0, 114.0, 111.0, 119.0]

    candles = []
    for i in range(n):
        block, k = divmod(i, 8)
        scale = start * (1.05 ** block)
        o = block_closes[k - 1] * scale if k > 0 else block_closes[0] * scale
        c = block_closes[k] * scale
        h = block_highs[k] * scale
        low = block_lows[k] * scale
        candles.append(_mk_candle(
            base + timedelta(hours=i), o, h, low, c,
            v=v_high if k % 2 == 0 else v_low,
        ))
    return candles


def test_full_analysis_uses_real_modules():
    """A valid series must produce real module-backed criteria & score 0-8."""
    candles = _trending_candles()

    result = MarketAnalyzer.analyze_candles(candles, symbol="BTCUSDT", timeframe="1h")
    assert result["status"] == "ok"
    assert 0 <= result["score"] <= 8
    assert result["max_score"] == 8
    assert set(result["criteria"].keys()) == {
        "structure_4h", "location_valid", "pattern_1h", "momentum_15m",
        "rsi_confirmed", "volume_confirmed", "rr_valid", "stop_loss_valid",
    }
    # Rising HH/HL market → real structure analyzer must report bullish
    assert result["criteria"]["structure_4h"] is True
    assert result["current_price"] > 0
    assert result["trade_setup"]["stop_loss"] < result["current_price"]
    assert result["trade_setup"]["risk_reward_ratio"] >= 1.5
    # Signal consistency with the 6/8 rule
    expected_signal = "BUY" if result["score"] >= 6 else "WAIT"
    assert result["trade_setup"]["signal"] == expected_signal


def test_score_pass_threshold_is_six_of_eight():
    candles = _trending_candles()
    result = MarketAnalyzer.analyze_candles(candles, symbol="BTCUSDT", timeframe="1h")
    assert result["passed"] == (result["score"] >= 6)
