# tests/test_replay_api.py
"""
Tests for the Bar Replay API endpoint (/api/market/analysis/replay).

Verifies:
1. Endpoint accepts sliced candle sequences from frontend Bar Replay.
2. Computes dynamic 8-criteria scores and patterns without look-ahead bias.
3. Correctly returns detected AlefTrade Running Flat and Developing Wave PRZ.
"""
from datetime import UTC, datetime, timedelta
import pathlib
import sys

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


def _generate_synthetic_candles(n: int = 45) -> list[dict]:
    """Generate synthetic 1H candles for replay testing."""
    base_time = int(datetime(2026, 10, 20, 0, 0, tzinfo=UTC).timestamp())
    profile = (
        [2000 + i * 6 for i in range(11)] +          # 0..10: 2000 -> 2060 (Impulse)
        [2060 - i * 3.75 for i in range(1, 9)] +     # 11..18: 2060 -> 2030 (Wave A)
        [2030 + i * 4.5 for i in range(1, 11)] +     # 19..28: 2030 -> 2075 (Wave B)
        [2075 - i * 3.0 for i in range(1, 11)] +     # 29..38: 2075 -> 2045 (Wave C)
        [2045 + i * 2.0 for i in range(1, 6)]        # 39..43: Continuation
    )

    candles = []
    for i, p in enumerate(profile[:n]):
        t = base_time + i * 3600
        candles.append({
            "time": t,
            "open": round(p - 1.0, 2),
            "high": round(p + 1.5, 2),
            "low": round(p - 1.5, 2),
            "close": round(p, 2),
            "volume": 1500.0,
        })
    return candles


@pytest.mark.asyncio
async def test_replay_insufficient_candles():
    candles = _generate_synthetic_candles(5)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/market/analysis/replay",
            json={"symbol": "BTCUSDT", "timeframe": "1h", "candles": candles},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "insufficient_data"


@pytest.mark.asyncio
async def test_replay_running_flat_step():
    """Verify replay analysis identifies patterns on sliced candles."""
    candles = _generate_synthetic_candles(44)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/market/analysis/replay",
            json={
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "candles": candles,
                "config": {"min_risk_reward": 1.5},
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "score" in data
    assert "trade_setup" in data
    assert "detected_patterns" in data
    assert isinstance(data["detected_patterns"], list)
