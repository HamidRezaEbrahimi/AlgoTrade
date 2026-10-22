# app/exchange/wallex_adapter.py
"""
Wallex Exchange Adapter (والکس).

Connects to Wallex Iranian Crypto Exchange REST API with multi-timeframe data.
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx

from app.exchange.base_adapter import BaseExchangeAdapter
from app.exchange.rate_limiter import AsyncRateLimiter, with_exchange_retry
from app.models.candle import Candle
from app.models.order import Order, OrderSide, OrderStatus, OrderType
from app.models.position import Position

logger = logging.getLogger("algotrade.exchange.wallex")


class WallexExchangeAdapter(BaseExchangeAdapter):
    """Wallex Exchange REST API Connector."""

    BASE_URL = "https://api.wallex.ir/v1"

    def __init__(self, api_key: str = "", api_secret: str = "") -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.order_rate_limiter = AsyncRateLimiter(min_interval_seconds=12.0)
        self.market_rate_limiter = AsyncRateLimiter(min_interval_seconds=0.1)
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"X-API-Key": self.api_key} if self.api_key else {},
            timeout=15.0,
        )

    @property
    def name(self) -> str:
        return "wallex"

    @with_exchange_retry(max_retries=3, rate_limit_pause_sec=30.0)
    async def get_balance(self) -> dict[str, Decimal]:
        await self.order_rate_limiter.wait_for_slot()
        try:
            resp = await self.client.get("/account/balances")
            data = resp.json()
            balances: dict[str, Decimal] = {}
            if "result" in data and "balances" in data["result"]:
                for asset, val in data["result"]["balances"].items():
                    balances[asset] = Decimal(str(val.get("value", "0")))
            return balances
        except Exception as e:
            logger.error(f"Wallex get_balance error: {e}")
            return {"USDT": Decimal("0"), "TMN": Decimal("0")}

    @with_exchange_retry(max_retries=3)
    async def get_symbols(self) -> list[dict[str, Any]]:
        """Fetch all available live symbols on Wallex."""
        def _sf(v: Any, d: float = 0.0) -> float:
            if v is None:
                return d
            try:
                s = str(v).strip()
                if s in ["-", "", "null", "None", "NaN"]:
                    return d
                return float(s)
            except Exception:
                return d

        await self.market_rate_limiter.wait_for_slot()
        try:
            resp = await self.client.get("/markets")
            data = resp.json()
            symbols_dict = data.get("result", {}).get("symbols", {})
            symbols: list[dict[str, Any]] = []
            for pair, info in symbols_dict.items():
                stats = info.get("stats", {}) or {}
                base = info.get("baseAsset") or (pair[:-4] if pair.endswith("USDT") else pair[:-3])
                quote = info.get("quoteAsset") or ("USDT" if pair.endswith("USDT") else "TMN")
                price = _sf(stats.get("lastPrice"))
                change_24h = _sf(stats.get("24h_ch"))
                fa_name = info.get("faName") or f"{base} - {quote}"
                en_name = info.get("enName") or f"{base} / {quote}"
                symbols.append({
                    "symbol": pair,
                    "raw_symbol": pair,
                    "name": fa_name,
                    "name_en": en_name,
                    "base": base,
                    "quote": quote,
                    "price": price,
                    "change24h": change_24h,
                    "exchange": "wallex",
                    "type": "toman" if quote in ["TMN", "IRT"] else "crypto",
                })
            return symbols
        except Exception as e:
            logger.error(f"Wallex get_symbols error: {e}")
            return []

    @with_exchange_retry(max_retries=3)
    async def get_ticker(self, symbol: str) -> dict[str, Decimal]:
        await self.market_rate_limiter.wait_for_slot()
        resp = await self.client.get("/markets")
        data = resp.json()
        pair_data = data.get("result", {}).get("symbols", {}).get(symbol, {})
        stats = pair_data.get("stats", {})
        last_price = Decimal(str(stats.get("lastPrice", "0")))
        return {
            "bid": Decimal(str(stats.get("bidPrice", last_price))),
            "ask": Decimal(str(stats.get("askPrice", last_price))),
            "last": last_price,
        }

    @with_exchange_retry(max_retries=3)
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        since: int | None = None,
        to_ts: int | None = None,
    ) -> list[Candle]:
        await self.market_rate_limiter.wait_for_slot()
        end_ts = to_ts if to_ts else int(time.time())
        tf_seconds = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "1h": 3600,
            "4h": 14400,
            "1d": 86400,
        }.get(timeframe, 3600)
        # Deep history allocation for lower timeframes
        target_limit = limit
        if timeframe in ["1m", "5m"] and target_limit < 1200:
            target_limit = 1200
        elif timeframe == "15m" and target_limit < 800:
            target_limit = 800

        from_ts = since if since else (end_ts - target_limit * tf_seconds)

        res_map = {
            "1m": "1",
            "5m": "15",
            "15m": "15",
            "30m": "60",
            "1h": "60",
            "4h": "240",
            "1d": "1D",
        }
        resolution = res_map.get(timeframe, "60")

        params = {
            "symbol": symbol,
            "resolution": resolution,
            "from": from_ts,
            "to": end_ts,
        }
        resp = await self.client.get("/udf/history", params=params)
        data = resp.json()

        candles: list[Candle] = []
        if data.get("s") == "ok":
            t_list = data.get("t", [])
            o_list = data.get("o", [])
            h_list = data.get("h", [])
            l_list = data.get("l", [])
            c_list = data.get("c", [])
            v_list = data.get("v", [])

            for i in range(len(t_list)):
                candles.append(
                    Candle(
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=datetime.fromtimestamp(t_list[i], tz=UTC),
                        open=Decimal(str(o_list[i])),
                        high=Decimal(str(h_list[i])),
                        low=Decimal(str(l_list[i])),
                        close=Decimal(str(c_list[i])),
                        volume=Decimal(str(v_list[i])),
                    )
                )
        return candles

    @with_exchange_retry(max_retries=3)
    async def create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        amount: Decimal,
        price: Decimal | None = None,
        client_order_id: str | None = None,
    ) -> Order:
        await self.order_rate_limiter.wait_for_slot()
        cid = client_order_id or str(uuid.uuid4())
        payload = {
            "symbol": symbol,
            "type": side.value.lower(),
            "execution_type": "LIMIT" if order_type == OrderType.LIMIT else "MARKET",
            "quantity": str(amount),
            "client_id": cid,
        }
        if price is not None:
            payload["price"] = str(price)

        resp = await self.client.post("/account/orders", json=payload)
        res_data = resp.json().get("result", {})

        return Order(
            id=uuid.uuid4(),
            client_order_id=cid,
            exchange_order_id=str(res_data.get("id", "")),
            symbol=symbol,
            exchange=self.name,
            side=side,
            order_type=order_type,
            status=OrderStatus.SUBMITTED,
            price=float(price) if price else None,
            amount=float(amount),
            filled=0.0,
            cost=0.0,
            fee=0.0,
            created_at=datetime.now(UTC),
        )

    async def cancel_order(self, order_id: str, symbol: str | None = None) -> bool:
        await self.order_rate_limiter.wait_for_slot()
        try:
            resp = await self.client.delete(f"/account/orders/{order_id}")
            return resp.status_code == 200
        except Exception:
            return False

    async def cancel_all_orders(self, symbol: str | None = None) -> list[str]:
        return []

    async def get_open_positions(self) -> list[Position]:
        return []

    async def close_position(self, position: Position) -> bool:
        close_side = OrderSide.SELL if position.direction.upper() == "LONG" else OrderSide.BUY
        await self.create_order(
            symbol=position.symbol,
            side=close_side,
            order_type=OrderType.MARKET,
            amount=Decimal(str(position.remaining_size)),
        )
        return True
