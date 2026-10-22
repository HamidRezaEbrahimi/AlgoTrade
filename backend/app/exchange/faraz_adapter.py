# app/exchange/faraz_adapter.py
"""
Faraz Data Feed Adapter (فراز).

Ingests Forex, Precious Metals, TSE Stock Exchange, and Crypto via Faraz TradingView API.
Implements robust timestamp math, resolution conversion, session cookie auth,
dynamic search & metadata resolution, and multi-domain failover rotation.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx

from app.config import get_settings
from app.exchange.base_adapter import BaseExchangeAdapter
from app.exchange.faraz_symbols import FARAZ_CATALOG_SYMBOLS, FARAZ_SYMBOL_MAP
from app.exchange.rate_limiter import AsyncRateLimiter, with_exchange_retry
from app.models.candle import Candle
from app.models.order import Order, OrderSide, OrderType
from app.models.position import Position

logger = logging.getLogger("algotrade.exchange.faraz")


def resolution_to_seconds(resolution: str) -> int:
    """Robust resolution to seconds converter."""
    r = resolution.upper()
    if r.isdigit():
        return int(r) * 60
    if r.endswith("S"):
        return int(r[:-1])
    if r.endswith("D") or r == "D":
        val = r[:-1] if r.endswith("D") and len(r) > 1 else "1"
        return int(val) * 86400
    if r.endswith("W") or r == "W":
        val = r[:-1] if r.endswith("W") and len(r) > 1 else "1"
        return int(val) * 604800
    if r.endswith("M") or r == "M":
        val = r[:-1] if r.endswith("M") and len(r) > 1 else "1"
        return int(val) * 2592000
    return 3600


async def sync_faraz_credentials_from_db() -> None:
    """Load active Faraz credentials from database into FarazDataAdapter defaults."""
    try:
        from app.db.database import async_session_factory
        from app.models.integration import IntegrationORM
        from sqlalchemy import select

        async with async_session_factory() as session:
            stmt = select(IntegrationORM).where(IntegrationORM.provider == "faraz")
            res = await session.execute(stmt)
            integrations = res.scalars().all()
            active = next((i for i in integrations if i.is_active and i.config), None)
            integration = active or next((i for i in integrations if i.config), None)

            if integration and integration.config:
                cfg = integration.config
                token = str(cfg.get("faraz_token", cfg.get("token", ""))).strip().replace("\r", "").replace("\n", "")
                cookie = str(cfg.get("faraz_cookie", cfg.get("cookie", ""))).strip().replace("\r", "").replace("\n", "")
                domain = str(cfg.get("faraz_domain", cfg.get("domain", ""))).strip()
                if token:
                    FarazDataAdapter.DEFAULT_TOKEN = token
                if cookie:
                    FarazDataAdapter.DEFAULT_COOKIE = cookie
                if domain and "sourcearena" not in domain:
                    FarazDataAdapter.DEFAULT_DOMAINS = [domain, "https://ir4.faraz.io", "https://faraz.io"]
                logger.info(f"🔑 Synced Faraz credentials from DB (Token: {bool(token)}, Cookie: {bool(cookie)})")
    except Exception as e:
        logger.warning(f"Could not sync Faraz credentials from DB: {e}")


class FarazDataAdapter(BaseExchangeAdapter):
    """Faraz API Market Data Adapter with session cookie and domain rotation."""

    DEFAULT_DOMAINS = [
        "https://ir4.faraz.io",
        "https://faraz.io",
    ]
    DEFAULT_COOKIE: str = ""
    DEFAULT_TOKEN: str = ""

    STATIC_SYMBOL_MAP: dict[str, str] = FARAZ_SYMBOL_MAP

    def __init__(
        self,
        domains: list[str] | None = None,
        token: str = "",
        cookie: str = "",
        adjust_type: str = "2",
        countback: int = 4800,
    ) -> None:
        settings = get_settings()
        self.domains = domains or [settings.faraz_api_domain_1, settings.faraz_api_domain_2, settings.faraz_api_domain_3]
        raw_token = token or settings.faraz_api_token.get_secret_value() or FarazDataAdapter.DEFAULT_TOKEN
        raw_cookie = cookie or settings.faraz_cookie.get_secret_value() or FarazDataAdapter.DEFAULT_COOKIE
        self.token = str(raw_token).strip().replace("\r", "").replace("\n", "")
        self.cookie = str(raw_cookie).strip().replace("\r", "").replace("\n", "")
        self.adjust_type = adjust_type
        self.countback = countback
        self.current_domain_idx = 0
        self.rate_limiter = AsyncRateLimiter(min_interval_seconds=0.5)
        self.client = httpx.AsyncClient(timeout=15.0)
        self.dynamic_symbol_cache: dict[str, str] = dict(self.STATIC_SYMBOL_MAP)

    @property
    def name(self) -> str:
        return "faraz"

    @property
    def current_base_url(self) -> str:
        return self.domains[self.current_domain_idx]

    def rotate_domain(self) -> None:
        old = self.current_base_url
        self.current_domain_idx = (self.current_domain_idx + 1) % len(self.domains)
        logger.warning(f"⚠️ Faraz Failover: {old} -> {self.current_base_url}")

    async def _ensure_credentials(self) -> None:
        """Ensure credentials are populated from DB if not already present."""
        if not (self.token and self.cookie):
            await sync_faraz_credentials_from_db()
            if FarazDataAdapter.DEFAULT_TOKEN and not self.token:
                self.token = FarazDataAdapter.DEFAULT_TOKEN
            if FarazDataAdapter.DEFAULT_COOKIE and not self.cookie:
                self.cookie = FarazDataAdapter.DEFAULT_COOKIE

    def _get_headers(self) -> dict[str, str]:
        token = (self.token or FarazDataAdapter.DEFAULT_TOKEN or "").strip().replace("\r", "").replace("\n", "")
        cookie = (self.cookie or FarazDataAdapter.DEFAULT_COOKIE or "").strip().replace("\r", "").replace("\n", "")
        headers = {
            "accept": "application/json, text/plain, */*",
            "origin": "https://faraz.io",
            "referer": "https://faraz.io/",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
        }
        if token:
            headers["x-access-token"] = token
        if cookie:
            headers["cookie"] = cookie
        return headers

    async def search_symbols(self, query: str) -> list[dict[str, Any]]:
        """Live search across all Faraz markets."""
        await self._ensure_credentials()
        if not query or not query.strip():
            return await self.get_symbols()

        q = query.strip()
        url = f"{self.current_base_url}/api/customer/trading-view/search"
        params = {"query": q, "type": "", "exchange": "", "limit": "40"}

        try:
            resp = await self.client.get(url, params=params, headers=self._get_headers())
            data = resp.json()
            if isinstance(data, list):
                results: list[dict[str, Any]] = []
                for item in data:
                    sym = item.get("symbol") or item.get("ticker", "")
                    name = item.get("full_name") or sym
                    desc = item.get("description") or name

                    self.dynamic_symbol_cache[sym.upper()] = sym
                    self.dynamic_symbol_cache[name.upper()] = sym
                    self.dynamic_symbol_cache[name] = sym

                    is_tse = sym.startswith("IR")
                    quote = "RLS" if is_tse else (
                        "USD" if any(c in sym for c in ["USD", "XAU", "XAG", "EUR", "GBP"]) else "TMN"
                    )

                    results.append({
                        "symbol": sym,
                        "raw_symbol": sym,
                        "name": desc,
                        "name_en": name,
                        "base": name,
                        "quote": quote,
                        "price": 0.0,
                        "change24h": 0.0,
                        "exchange": "faraz",
                        "type": "tse" if is_tse else "gold_forex",
                    })
                return results
        except Exception as e:
            logger.warning(f"Faraz search error for '{q}': {e}")

        return await self.get_symbols()

    async def _resolve_symbol(self, raw_symbol: str) -> str:
        """Resolve any ticker/name to exact Faraz symbolName."""
        clean = raw_symbol.strip()
        clean_upper = clean.upper()

        if clean in self.dynamic_symbol_cache:
            return self.dynamic_symbol_cache[clean]
        if clean_upper in self.dynamic_symbol_cache:
            return self.dynamic_symbol_cache[clean_upper]

        if clean_upper.startswith("IR") or "_" in clean:
            return clean_upper

        try:
            results = await self.search_symbols(clean)
            if results:
                target = str(results[0]["symbol"])
                self.dynamic_symbol_cache[clean] = target
                self.dynamic_symbol_cache[clean_upper] = target
                return target
        except Exception:
            pass

        return clean_upper

    @with_exchange_retry(max_retries=3)
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 300,
        since: int | None = None,
        to_ts: int | None = None,
    ) -> list[Candle]:
        await self._ensure_credentials()
        await self.rate_limiter.wait_for_slot()

        # Resolution mapping
        res_map = {
            "1m": "1",
            "3m": "3",
            "5m": "5",
            "15m": "15",
            "30m": "30",
            "1h": "60",
            "2h": "120",
            "4h": "240",
            "1d": "D",
            "1w": "W",
        }
        tf_clean = timeframe.lower().strip()
        resolution = res_map.get(
            tf_clean,
            "3" if tf_clean in ["3", "3m"] else ("D" if symbol.startswith("IR") else "60"),
        )
        faraz_symbol = await self._resolve_symbol(symbol)

        res_seconds = resolution_to_seconds(resolution)
        now_ts = int(datetime.now(UTC).timestamp())
        target_to = to_ts or now_ts
        target_count = max(limit, self.countback)
        calc_from = since or max(0, target_to - (target_count * res_seconds))

        url = f"{self.current_base_url}/api/customer/trading-view/history"
        params = {
            "symbolName": faraz_symbol,
            "resolution": resolution,
            "from": str(calc_from),
            "to": str(target_to),
            "countback": str(target_count),
            "firstDataRequest": "true" if not to_ts else "false",
            "latest": "false",
            "adjustType": self.adjust_type,
            "json": "true",
        }

        try:
            resp = await self.client.get(url, params=params, headers=self._get_headers())
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and data.get("success") is False:
                raise Exception(data.get("message", "Unknown API Error"))
        except Exception as e:
            self.rotate_domain()
            raise e

        candles: list[Candle] = []
        res_data = data.get("result") if (isinstance(data, dict) and "result" in data) else data

        if isinstance(res_data, dict):
            t_list = res_data.get("t", [])
            o_list = res_data.get("o", [])
            h_list = res_data.get("h", [])
            l_list = res_data.get("l", [])
            c_list = res_data.get("c", [])
            v_list = res_data.get("v", []) or [0] * len(t_list)

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

        if to_ts:
            candles = [c for c in candles if int(c.timestamp.timestamp()) <= to_ts]

        return candles[-limit:] if limit and len(candles) > limit else candles

    async def get_symbols(self) -> list[dict[str, Any]]:
        """Return catalog of top Faraz markets."""
        return list(FARAZ_CATALOG_SYMBOLS)

    async def get_balance(self) -> dict[str, Decimal]:
        return {}

    async def get_ticker(self, symbol: str) -> dict[str, Decimal]:
        candles = await self.get_candles(
            symbol, "1d" if symbol.startswith("IR") else "15m", limit=1
        )
        if candles:
            last = candles[-1].close
            return {"bid": last, "ask": last, "last": last}
        return {"bid": Decimal("0"), "ask": Decimal("0"), "last": Decimal("0")}

    async def create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        amount: Decimal,
        price: Decimal | None = None,
        client_order_id: str | None = None,
    ) -> Order:
        raise NotImplementedError("Faraz is a pure market data provider, not an execution broker.")

    async def cancel_order(self, order_id: str, symbol: str | None = None) -> bool:
        return False

    async def cancel_all_orders(self, symbol: str | None = None) -> list[str]:
        return []

    async def get_open_positions(self) -> list[Position]:
        return []

    async def close_position(self, position: Position) -> bool:
        return False
