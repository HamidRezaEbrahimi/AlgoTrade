# app/api/routes_settings.py
"""
Settings and Exchange Configuration REST Endpoints.

Allows managing API tokens, Faraz session cookie, exchange credentials, and safe trading controls.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_settings
from app.exchange.faraz_adapter import FarazDataAdapter
from app.exchange.nobitex_adapter import NobitexExchangeAdapter
from app.exchange.wallex_adapter import WallexExchangeAdapter

logger = logging.getLogger("algotrade.api.settings")
router = APIRouter(prefix="/settings", tags=["Settings & Credentials"])


class ExchangeCredentialsPayload(BaseModel):
    """Payload for updating exchange credentials and tokens."""
    faraz_token: str | None = Field(default=None, description="Faraz JWT Access Token")
    faraz_cookie: str | None = Field(default=None, description="Faraz Full Browser Session Cookie")
    faraz_domain: str | None = Field(default=None, description="Preferred Faraz API base domain (e.g. https://ir4.faraz.io)")
    faraz_countback: int | None = Field(default=None, description="Default candle countback (e.g. 4800)")
    faraz_adjust_type: str | None = Field(default=None, description="Faraz adjust type (e.g. '2')")
    wallex_api_key: str | None = Field(default=None, description="Wallex API Key")
    wallex_secret: str | None = Field(default=None, description="Wallex API Secret")
    nobitex_token: str | None = Field(default=None, description="Nobitex API Token")
    auto_trading_enabled: bool | None = Field(default=False, description="Master Auto-Trading toggle")
    max_risk_per_trade_pct: float | None = Field(default=1.0, ge=0.1, le=5.0)


class ConnectionTestRequest(BaseModel):
    """Payload for testing an exchange connection."""
    exchange: str = Field(..., description="'faraz', 'wallex', or 'nobitex'")
    token_or_key: str | None = None
    secret: str | None = None
    cookie: str | None = None
    domain: str | None = None


# In-memory runtime settings cache (seeded from environment & Faraz defaults)
settings = get_settings()
runtime_config: dict[str, Any] = {
    "faraz_token": settings.faraz_api_token.get_secret_value(),
    "faraz_cookie": settings.faraz_cookie.get_secret_value(),
    "faraz_domain": settings.faraz_api_domain_1,
    "faraz_countback": 4800,
    "faraz_adjust_type": "2",
    "wallex_api_key": settings.wallex_api_key.get_secret_value(),
    "wallex_secret": settings.wallex_secret.get_secret_value(),
    "nobitex_token": settings.nobitex_api_key.get_secret_value(),
    "auto_trading_enabled": False,  # Strict Safety default: LOCKED
    "max_risk_per_trade_pct": 1.0,
}


@router.get("/exchanges")
async def get_exchange_settings() -> dict[str, Any]:
    """Return current exchange connection statuses and masked credentials."""
    def mask(val: str) -> str:
        if not val:
            return ""
        if len(val) <= 8:
            return "******"
        return f"{val[:4]}...{val[-4:]}"

    return {
        "faraz": {
            "has_token": bool(runtime_config.get("faraz_token")),
            "token_masked": mask(runtime_config.get("faraz_token", "")),
            "has_cookie": bool(runtime_config.get("faraz_cookie")),
            "cookie_masked": mask(runtime_config.get("faraz_cookie", "")),
            "domain": runtime_config.get("faraz_domain", "https://ir4.faraz.io"),
            "countback": runtime_config.get("faraz_countback", 4800),
            "adjust_type": runtime_config.get("faraz_adjust_type", "2"),
            "status": "connected" if (runtime_config.get("faraz_token") or runtime_config.get("faraz_cookie")) else "unconfigured",
        },
        "wallex": {
            "has_key": bool(runtime_config.get("wallex_api_key")),
            "key_masked": mask(runtime_config.get("wallex_api_key", "")),
            "has_secret": bool(runtime_config.get("wallex_secret")),
            "status": "ready" if runtime_config.get("wallex_api_key") else "public_feed_only",
        },
        "nobitex": {
            "has_token": bool(runtime_config.get("nobitex_token")),
            "token_masked": mask(runtime_config.get("nobitex_token", "")),
            "status": "ready" if runtime_config.get("nobitex_token") else "public_feed_only",
        },
        "safety": {
            "auto_trading_enabled": runtime_config.get("auto_trading_enabled", False),
            "trading_mode": settings.trading_mode.value,
            "max_risk_per_trade_pct": runtime_config.get("max_risk_per_trade_pct", 1.0),
        },
    }


@router.post("/exchanges")
async def update_exchange_settings(payload: ExchangeCredentialsPayload) -> dict[str, Any]:
    """Update runtime exchange tokens, Faraz cookies, and safety settings."""
    if payload.faraz_token is not None:
        runtime_config["faraz_token"] = payload.faraz_token.strip()
    if payload.faraz_cookie is not None:
        runtime_config["faraz_cookie"] = payload.faraz_cookie.strip()
    if payload.faraz_domain is not None:
        runtime_config["faraz_domain"] = payload.faraz_domain.strip()
    if payload.faraz_countback is not None:
        runtime_config["faraz_countback"] = payload.faraz_countback
    if payload.faraz_adjust_type is not None:
        runtime_config["faraz_adjust_type"] = payload.faraz_adjust_type.strip()
    if payload.wallex_api_key is not None:
        runtime_config["wallex_api_key"] = payload.wallex_api_key.strip()
    if payload.wallex_secret is not None:
        runtime_config["wallex_secret"] = payload.wallex_secret.strip()
    if payload.nobitex_token is not None:
        runtime_config["nobitex_token"] = payload.nobitex_token.strip()
    if payload.auto_trading_enabled is not None:
        runtime_config["auto_trading_enabled"] = payload.auto_trading_enabled
    if payload.max_risk_per_trade_pct is not None:
        runtime_config["max_risk_per_trade_pct"] = payload.max_risk_per_trade_pct

    logger.info("⚙️ Exchange credentials and Faraz session parameters updated.")
    return {"status": "ok", "message": "Settings updated successfully"}


@router.post("/test-connection")
async def test_exchange_connection(payload: ConnectionTestRequest) -> dict[str, Any]:
    """Ping exchange endpoint and verify token/cookie validity."""
    exchange = payload.exchange.lower()

    if exchange == "faraz":
        token = payload.token_or_key or runtime_config.get("faraz_token", "")
        cookie = payload.cookie or runtime_config.get("faraz_cookie", "")
        domain = payload.domain or runtime_config.get("faraz_domain") or "https://ir4.faraz.io"
        countback = runtime_config.get("faraz_countback", 4800)
        adjust_type = runtime_config.get("faraz_adjust_type", "2")

        adapter = FarazDataAdapter(
            domains=[domain],
            token=token,
            cookie=cookie,
            countback=countback,
            adjust_type=adjust_type,
        )
        try:
            candles = await adapter.get_candles("XAG_USD", "15m", limit=5)
            if candles:
                return {
                    "status": "success",
                    "exchange": "faraz",
                    "message": f"اتصال به فراز برقرار است. {len(candles)} کندل زنده با موفقیت دریافت شد.",
                }
            return {
                "status": "error",
                "exchange": "faraz",
                "message": "پاسخی از اندپوینت فراز دریافت نشد. لطفاً کوکی سشن یا آدرس دامنه را بررسی کنید.",
            }
        except Exception as e:
            return {"status": "error", "exchange": "faraz", "message": f"خطا در اتصال به فراز: {str(e)}"}

    elif exchange == "wallex":
        key = payload.token_or_key or runtime_config.get("wallex_api_key", "")
        secret = payload.secret or runtime_config.get("wallex_secret", "")
        adapter = WallexExchangeAdapter(api_key=key, api_secret=secret)
        try:
            ticker = await adapter.get_ticker("BTCUSDT")
            price = float(ticker.get("last", 0))
            if price > 0:
                return {"status": "success", "exchange": "wallex", "message": f"Wallex connection active. Last BTC price: ${price:,.2f}"}
            return {"status": "error", "exchange": "wallex", "message": "Could not fetch ticker price."}
        except Exception as e:
            return {"status": "error", "exchange": "wallex", "message": f"Connection failed: {str(e)}"}

    elif exchange == "nobitex":
        token = payload.token_or_key or runtime_config.get("nobitex_token", "")
        adapter = NobitexExchangeAdapter(api_token=token)
        try:
            ticker = await adapter.get_ticker("BTCUSDT")
            price = float(ticker.get("last", 0))
            if price > 0:
                return {"status": "success", "exchange": "nobitex", "message": f"Nobitex connection active. Last BTC price: ${price:,.2f}"}
            return {"status": "error", "exchange": "nobitex", "message": "Could not fetch Nobitex ticker price."}
        except Exception as e:
            return {"status": "error", "exchange": "nobitex", "message": f"Connection failed: {str(e)}"}

    raise HTTPException(status_code=400, detail=f"Unsupported exchange '{exchange}'")
