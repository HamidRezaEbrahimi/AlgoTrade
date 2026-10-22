# app/market_data/candle_buffer.py
"""
Ring Buffer for Candle Storage.

Rule:
- Strict capacity limit: 1,000 candles per symbol per timeframe.
- Zero memory leaks over long running sessions.
"""
from __future__ import annotations

from collections import deque

from app.models.candle import Candle


class CandleRingBuffer:
    """Fixed-capacity ring buffer for storing closed candles."""

    def __init__(self, capacity: int = 1000) -> None:
        self.capacity = capacity
        # Mapping: (symbol, timeframe) -> deque of Candle
        self._buffers: dict[tuple[str, str], deque[Candle]] = {}

    def _get_key(self, symbol: str, timeframe: str) -> tuple[str, str]:
        return (symbol.upper(), timeframe.lower())

    def add_candle(self, candle: Candle) -> None:
        """Add a closed candle to the ring buffer."""
        key = self._get_key(candle.symbol, candle.timeframe)
        if key not in self._buffers:
            self._buffers[key] = deque(maxlen=self.capacity)

        buf = self._buffers[key]
        # Avoid duplicate timestamp if already present at the end
        if buf and buf[-1].timestamp == candle.timestamp:
            buf[-1] = candle  # update in place
        else:
            buf.append(candle)

    def add_candles(self, candles: list[Candle]) -> None:
        """Bulk add candles in chronological order."""
        for c in candles:
            self.add_candle(c)

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int | None = None,
    ) -> list[Candle]:
        """Retrieve recent candles up to limit."""
        key = self._get_key(symbol, timeframe)
        buf = self._buffers.get(key, deque())
        if limit is None:
            return list(buf)
        return list(buf)[-limit:]

    def get_arrays(
        self,
        symbol: str,
        timeframe: str,
        limit: int | None = None,
    ) -> tuple[list[float], list[float], list[float], list[float], list[float]]:
        """
        Return (opens, highs, lows, closes, volumes) as float arrays for fast indicator computation.
        """
        candles = self.get_candles(symbol, timeframe, limit)
        opens = [float(c.open) for c in candles]
        highs = [float(c.high) for c in candles]
        lows = [float(c.low) for c in candles]
        closes = [float(c.close) for c in candles]
        volumes = [float(c.volume) for c in candles]
        return opens, highs, lows, closes, volumes
