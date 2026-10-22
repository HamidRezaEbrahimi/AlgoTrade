# app/market_data/multi_tf.py
"""
Multi-Timeframe Data Aggregator.

Prepares closed candle structures for 4H, 1H, and 15M timeframes.
"""
from __future__ import annotations

from app.market_data.candle_buffer import CandleRingBuffer
from app.strategy.signal_scorer import MultiTimeframeCandles


class MultiTimeframeManager:
    """Coordinates multi-timeframe candle retrieval from ring buffers."""

    def __init__(self, buffer: CandleRingBuffer) -> None:
        self.buffer = buffer

    def get_strategy_payload(self, symbol: str) -> MultiTimeframeCandles | None:
        """
        Extract multi-timeframe arrays for the strategy engine.
        Returns None if any required timeframe has insufficient closed candles.
        """
        _, h4_h, h4_l, h4_c, _ = self.buffer.get_arrays(symbol, "4h", limit=100)
        h1_o, h1_h, h1_l, h1_c, h1_v = self.buffer.get_arrays(symbol, "1h", limit=100)
        _, _, _, m15_c, m15_v = self.buffer.get_arrays(symbol, "15m", limit=50)

        # Minimum bar requirements
        if len(h4_c) < 15 or len(h1_c) < 20 or len(m15_c) < 15:
            return None

        return MultiTimeframeCandles(
            h4_highs=h4_h,
            h4_lows=h4_l,
            h4_closes=h4_c,
            h1_opens=h1_o,
            h1_highs=h1_h,
            h1_lows=h1_l,
            h1_closes=h1_c,
            h1_volumes=h1_v,
            m15_closes=m15_c,
            m15_volumes=m15_v,
        )
