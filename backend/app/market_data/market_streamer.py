# app/market_data/market_streamer.py
"""
Real-Time Market Ingestion & WebSocket Streamer Engine.

Solves the lack of WebSocket in Faraz/UDF REST feeds:
- Polls live tickers and latest candles at configurable intervals.
- Ingests into CandleRingBuffer for strategy execution.
- Broadcasts real-time tick and candle updates via WebSocket (/ws).
- Evaluates 8-criteria signal scanner on closed candles and emits qualified opportunities.
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from datetime import UTC, datetime

from app.api.ws_handler import ws_manager
from app.exchange.faraz_adapter import FarazDataAdapter
from app.exchange.nobitex_adapter import NobitexExchangeAdapter
from app.exchange.wallex_adapter import WallexExchangeAdapter
from app.market_data.candle_buffer import CandleRingBuffer
from app.market_data.multi_tf import MultiTimeframeManager
from app.market_data.scanner import MarketScanner

logger = logging.getLogger("algotrade.market_streamer")


class MarketStreamer:
    """Background engine fetching real market data and streaming over WebSocket."""

    DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "EURUSD", "XAUUSD"]
    DEFAULT_TIMEFRAMES = ["15m", "1h", "4h"]

    def __init__(
        self,
        buffer: CandleRingBuffer,
        tf_manager: MultiTimeframeManager,
        poll_interval_sec: float = 2.5,
        scan_interval_sec: float = 900.0,
    ) -> None:
        self.buffer = buffer
        self.tf_manager = tf_manager
        self.scanner = MarketScanner(tf_manager)
        self.poll_interval_sec = poll_interval_sec
        # Strategy scans run every 15 minutes ONLY after a candle close
        # (AGENTS.md rule 5.5) — never intra-candle.
        self.scan_interval_sec = scan_interval_sec
        self._last_scan_time: float = 0.0
        self._last_candle_open_ts: int | None = None
        self.faraz = FarazDataAdapter()
        self.wallex = WallexExchangeAdapter()
        self.nobitex = NobitexExchangeAdapter()
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self.latest_prices: dict[str, float] = {}
        self.subscribed_symbols: set[str] = set(self.DEFAULT_SYMBOLS)

    def subscribe_symbol(self, symbol: str) -> None:
        """Register a new symbol for continuous live tick polling."""
        if symbol:
            clean = symbol.upper().strip()
            if clean not in self.subscribed_symbols:
                self.subscribed_symbols.add(clean)
                logger.info(f"📡 Subscribed new live symbol to streamer: {clean}")

    async def start(self) -> None:
        """Start the background streaming worker."""
        if self._running:
            return
        self._running = True
        logger.info("🚀 Starting Real-Time Market Streamer Worker...")
        self._task = asyncio.create_task(self._bootstrap_and_run())

    async def _bootstrap_and_run(self) -> None:
        """Seed history then run continuous streaming loop."""
        try:
            await self._seed_initial_history()
        except Exception as e:
            logger.warning(f"Error during initial candle seeding: {e}")
        await self._run_loop()

    async def stop(self) -> None:
        """Stop the background streaming worker."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("🛑 Real-Time Market Streamer stopped.")

    async def _seed_initial_history(self) -> None:
        """Pre-fetch history for all active symbols and timeframes."""
        for sym in self.DEFAULT_SYMBOLS:
            for tf in self.DEFAULT_TIMEFRAMES:
                try:
                    candles = await self.fetch_real_candles(sym, tf, limit=100)
                    if candles:
                        self.buffer.add_candles(candles)
                        logger.info(
                            f"📊 Ingested {len(candles)} real candles for {sym} [{tf}]"
                        )
                except Exception as e:
                    logger.warning(
                        f"Initial seed error for {sym} [{tf}]: {e}"
                    )

    async def fetch_real_candles(
        self, symbol: str, timeframe: str, limit: int = 100
    ):
        """Fetch candles with proper exchange routing."""
        clean = symbol.upper()
        is_forex_metal_tse = any(k in clean for k in ["EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD", "XAU", "XAG", "GOLD", "SILVER", "IRO1", "FOLD", "MSMI", "IKCO", "SIPA"])

        # 1. Forex, Metals, and TSE are exclusive to Faraz
        if is_forex_metal_tse:
            try:
                candles = await self.faraz.get_candles(symbol, timeframe, limit=limit)
                if candles:
                    return candles
            except Exception as e:
                logger.debug(f"Faraz candles error for {symbol}: {e}")
            return []

        # 2. Crypto pairs: Wallex -> Nobitex -> Faraz fallback
        try:
            candles = await self.wallex.get_candles(symbol, timeframe, limit=limit)
            if candles:
                return candles
        except Exception as e:
            logger.debug(f"Wallex candles fallback for {symbol}: {e}")

        try:
            candles = await self.nobitex.get_candles(symbol, timeframe, limit=limit)
            if candles:
                return candles
        except Exception as e:
            logger.debug(f"Nobitex candles fallback for {symbol}: {e}")

        try:
            candles = await self.faraz.get_candles(symbol, timeframe, limit=limit)
            if candles:
                return candles
        except Exception:
            pass

        return []

    async def fetch_real_ticker(self, symbol: str) -> float:
        """Fetch current price ticker with proper exchange routing."""
        clean = symbol.upper()
        is_forex_metal_tse = any(k in clean for k in ["EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD", "XAU", "XAG", "GOLD", "SILVER", "IRO1", "FOLD", "MSMI", "IKCO", "SIPA"])

        # 1. Forex / Metals / TSE
        if is_forex_metal_tse:
            try:
                ticker = await self.faraz.get_ticker(symbol)
                price = float(ticker.get("last", 0))
                if price > 0:
                    return price
            except Exception:
                pass
            return 0.0

        # 2. Crypto ticker: Wallex -> Nobitex
        try:
            ticker = await self.wallex.get_ticker(symbol)
            price = float(ticker.get("last", 0))
            if price > 0:
                return price
        except Exception:
            pass

        try:
            ticker = await self.nobitex.get_ticker(symbol)
            price = float(ticker.get("last", 0))
            if price > 0:
                return price
        except Exception:
            pass

        return self.latest_prices.get(symbol, 0.0)

    async def _run_loop(self) -> None:
        """Continuous polling and WebSocket broadcast loop."""
        while self._running:
            try:
                candle_just_closed = False
                for sym in list(self.subscribed_symbols):
                    price = await self.fetch_real_ticker(sym)
                    if price > 0:
                        self.latest_prices[sym] = price

                        # Broadcast live tick over WebSocket
                        await ws_manager.broadcast_global(
                            {
                                "type": "tick",
                                "symbol": sym,
                                "price": price,
                                "timestamp": datetime.now(
                                    UTC
                                ).isoformat(),
                            }
                        )

                    # Update 15M / 1H latest candle in ring buffer
                    try:
                        latest_15m = await self.fetch_real_candles(
                            sym, "15m", limit=5
                        )
                        if latest_15m:
                            for c in latest_15m:
                                self.buffer.add_candle(c)
                            # Broadcast latest candle update
                            last_c = latest_15m[-1]
                            candle_open_ts = int(
                                last_c.timestamp.timestamp()
                            )
                            # Detect 15m candle close: a new candle open
                            # timestamp means the previous candle closed.
                            candle_just_closed = (
                                self._last_candle_open_ts is not None
                                and candle_open_ts > self._last_candle_open_ts
                            )
                            self._last_candle_open_ts = candle_open_ts
                            await ws_manager.broadcast_global(
                                {
                                    "type": "candle_update",
                                    "symbol": sym,
                                    "timeframe": "15m",
                                    "candle": {
                                        "time": int(
                                            last_c.timestamp.timestamp()
                                        ),
                                        "open": float(last_c.open),
                                        "high": float(last_c.high),
                                        "low": float(last_c.low),
                                        "close": float(last_c.close),
                                        "volume": float(last_c.volume),
                                    },
                                }
                            )
                    except Exception as e:
                        logger.debug(f"Candle poll error: {e}")

                # Run opportunity scanner ONLY after a 15m candle close and
                # at most once per scan_interval (15 min) — AGENTS.md 5.5.
                symbols_with_prices = [
                    (s, p) for s, p in self.latest_prices.items() if p > 0
                ]
                now = time.time()
                interval_elapsed = (
                    now - self._last_scan_time
                ) >= self.scan_interval_sec
                if (
                    symbols_with_prices
                    and candle_just_closed
                    and interval_elapsed
                ):
                    self._last_scan_time = now
                    opps = self.scanner.scan_all_symbols(symbols_with_prices)
                    if opps:
                        await ws_manager.broadcast_global(
                            {
                                "type": "opportunities_update",
                                "opportunities": [
                                    {
                                        "symbol": o.symbol,
                                        "direction": o.direction,
                                        "total_score": o.total_score,
                                        "is_ready_to_enter": o.is_ready_to_enter,
                                        "current_price": o.current_price,
                                        "stop_loss": o.stop_loss,
                                        "take_profit": o.take_profit,
                                        "risk_reward": o.risk_reward,
                                        "reason_fa": o.reason_fa,
                                    }
                                    for o in opps
                                ],
                            }
                        )

            except Exception as e:
                logger.error(f"Market Streamer loop error: {e}")

            await asyncio.sleep(self.poll_interval_sec)


# Global singleton streamer instance
global_market_streamer: MarketStreamer | None = None


def get_market_streamer(
    buffer: CandleRingBuffer | None = None,
    tf_manager: MultiTimeframeManager | None = None,
) -> MarketStreamer:
    """Get or create singleton MarketStreamer."""
    global global_market_streamer
    if global_market_streamer is None:
        buf = buffer or CandleRingBuffer(capacity=1000)
        tfm = tf_manager or MultiTimeframeManager(buf)
        global_market_streamer = MarketStreamer(buf, tfm)
    return global_market_streamer
