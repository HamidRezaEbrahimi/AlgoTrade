# app/exchange/nobitex_adapter.py
"""
Nobitex Exchange Adapter (نوبیتکس).

Connects to Nobitex Iranian Crypto Exchange API with multi-timeframe deep data.
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

logger = logging.getLogger("algotrade.exchange.nobitex")


class NobitexExchangeAdapter(BaseExchangeAdapter):
    """Nobitex Exchange REST API Connector."""

    BASE_URL = "https://apiv2.nobitex.ir"

    def __init__(self, api_token: str = "") -> None:
        self.api_token = api_token
        self.order_rate_limiter = AsyncRateLimiter(min_interval_seconds=12.0)
        self.market_rate_limiter = AsyncRateLimiter(min_interval_seconds=0.05)
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Token {self.api_token}"} if self.api_token else {},
            timeout=15.0,
        )

    @property
    def name(self) -> str:
        return "nobitex"

    @with_exchange_retry(max_retries=3, rate_limit_pause_sec=30.0)
    async def get_balance(self) -> dict[str, Decimal]:
        await self.order_rate_limiter.wait_for_slot()
        try:
            resp = await self.client.post("/users/wallets/list")
            data = resp.json()
            balances: dict[str, Decimal] = {}
            if data.get("status") == "ok":
                for wallet in data.get("wallets", []):
                    currency = wallet.get("currency", "").upper()
                    balances[currency] = Decimal(str(wallet.get("balance", "0")))
            return balances
        except Exception as e:
            logger.error(f"Nobitex get_balance error: {e}")
            return {"USDT": Decimal("0"), "RLS": Decimal("0")}

    @with_exchange_retry(max_retries=3)
    async def get_symbols(self) -> list[dict[str, Any]]:
        """Fetch all available live symbols on Nobitex."""
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
            resp = await self.client.get("/market/stats")
            data = resp.json()
            stats = data.get("stats", {})
            symbols: list[dict[str, Any]] = []
            for pair, stat in stats.items():
                if not stat or not isinstance(stat, dict):
                    continue
                parts = pair.split("-")
                base = parts[0].upper() if len(parts) > 0 else pair
                quote = parts[1].upper() if len(parts) > 1 else "USDT"
                price = _sf(stat.get("latest"))
                change_24h = _sf(stat.get("dayChange"))
                symbols.append({
                    "symbol": f"{base}{quote}",
                    "raw_symbol": pair,
                    "name": f"{base} - {quote}",
                    "name_en": f"{base} / {quote}",
                    "base": base,
                    "quote": quote,
                    "price": price,
                    "change24h": change_24h,
                    "exchange": "nobitex",
                    "type": "toman" if quote in ["RLS", "TMN"] else "crypto",
                })
            return symbols
        except Exception as e:
            logger.error(f"Nobitex get_symbols error: {e}")
            return []

    @with_exchange_retry(max_retries=3)
    async def get_ticker(self, symbol: str) -> dict[str, Decimal]:
        await self.market_rate_limiter.wait_for_slot()
        nobitex_symbol = symbol.lower()
        if "usdt" in nobitex_symbol and "-" not in nobitex_symbol:
            nobitex_symbol = nobitex_symbol.replace("usdt", "-usdt")
        elif "rls" in nobitex_symbol and "-" not in nobitex_symbol:
            nobitex_symbol = nobitex_symbol.replace("rls", "-rls")

        src = nobitex_symbol.split("-")[0] if "-" in nobitex_symbol else nobitex_symbol
        dst = nobitex_symbol.split("-")[1] if "-" in nobitex_symbol else "usdt"
        resp = await self.client.get(f"/market/stats?srcCurrency={src}&dstCurrency={dst}")
        data = resp.json()
        stats = data.get("stats", {}).get(f"{src}-{dst}", {})
        last_price = Decimal(str(stats.get("latest", "0")))
        return {
            "bid": Decimal(str(stats.get("bestBuy", last_price))),
            "ask": Decimal(str(stats.get("bestSell", last_price))),
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
        res_map = {
            "1m": "1",
            "5m": "5",
            "15m": "15",
            "30m": "30",
            "1h": "60",
            "4h": "240",
            "1d": "D",
        }
        resolution = res_map.get(timeframe, "60")
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
        if timeframe in ["1m", "5m"] and target_limit < 1000:
            target_limit = 1000
        elif timeframe == "15m" and target_limit < 600:
            target_limit = 600

        chunks_count = min(max(1, (target_limit + 499) // 500), 3)

        clean_symbol = symbol.upper()
        if clean_symbol.endswith("RLS") or clean_symbol.endswith("TMN"):
            clean_symbol = clean_symbol[:-3] + "IRT"

        items = []
        seen_t = set()

        for c_idx in range(chunks_count):
            to_chunk = end_ts - c_idx * 500 * tf_seconds
            from_chunk = to_chunk - 500 * tf_seconds
            if since and from_chunk < since:
                from_chunk = since
            params = {
                "symbol": clean_symbol,
                "resolution": resolution,
                "from": from_chunk,
                "to": to_chunk,
            }
            try:
                resp = await self.client.get("/market/udf/history", params=params)
                data = resp.json()
                if data.get("s") == "ok":
                    t_list = data.get("t", [])
                    o_list = data.get("o", [])
                    h_list = data.get("h", [])
                    l_list = data.get("l", [])
                    c_list = data.get("c", [])
                    v_list = data.get("v", [])
                    for i in range(len(t_list)):
                        ts = t_list[i]
                        if ts not in seen_t:
                            seen_t.add(ts)
                            items.append((
                                ts,
                                Decimal(str(o_list[i])),
                                Decimal(str(h_list[i])),
                                Decimal(str(l_list[i])),
                                Decimal(str(c_list[i])),
                                Decimal(str(v_list[i])),
                            ))
            except Exception:
                pass

        # Sort by timestamp ascending
        items.sort(key=lambda x: x[0])
        candles: list[Candle] = [
            Candle(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=datetime.fromtimestamp(item[0], tz=UTC),
                open=item[1],
                high=item[2],
                low=item[3],
                close=item[4],
                volume=item[5],
            )
            for item in items
        ]
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
        src, dst = symbol.split("/") if "/" in symbol else (symbol[:-4], symbol[-4:])
        payload = {
            "type": "buy" if side == OrderSide.BUY else "sell",
            "execution": "limit" if order_type == OrderType.LIMIT else "market",
            "srcCurrency": src.lower(),
            "dstCurrency": dst.lower(),
            "amount": str(amount),
        }
        if price is not None:
            payload["price"] = str(price)

        resp = await self.client.post("/market/orders/add", json=payload)
        res_data = resp.json().get("order", {})

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
            resp = await self.client.post("/market/orders/update-status", json={"order": order_id, "status": "canceled"})
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
