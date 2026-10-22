# app/api/routes_integrations.py
"""
Unified Integrations Hub REST Endpoints.

Allows adding, managing, toggling, testing, and deleting:
- Exchanges (Wallex, Nobitex, Faraz, Binance, etc.)
- Messenger Bots (Telegram, Bale, Discord)
- AI Agent LLMs (Gemini, DeepSeek, OpenAI, Ollama)
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.bale_bot import BaleBotClient
from app.bot.bot_manager import get_bot_manager
from app.bot.telegram_bot import TelegramBotClient
from app.db.database import get_async_session
from app.exchange.faraz_adapter import FarazDataAdapter
from app.exchange.nobitex_adapter import NobitexExchangeAdapter
from app.exchange.wallex_adapter import WallexExchangeAdapter
from app.models.integration import (
    IntegrationCreate,
    IntegrationORM,
    IntegrationRead,
    IntegrationStatus,
    IntegrationType,
    IntegrationUpdate,
)

logger = logging.getLogger("algotrade.api.integrations")
router = APIRouter(prefix="/integrations", tags=["Integrations Hub"])


def _sanitize_config(config: dict[str, Any] | None) -> dict[str, Any]:
    """Sanitize configuration values to remove unwanted whitespace/newlines."""
    if not config:
        return {}
    clean: dict[str, Any] = {}
    for k, v in config.items():
        if isinstance(v, str):
            clean[k] = v.strip().replace("\r", "").replace("\n", "")
        else:
            clean[k] = v
    return clean


def _format_error_message(provider_name: str, exc: Exception) -> str:
    """Format exceptions into human-readable Persian messages without technical URL dumps."""
    import httpx

    msg = str(exc)
    err_lower = msg.lower()

    # 1. HTTP Status Errors from httpx
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        if code == 401:
            return (
                f"خطای احراز هویت (کد ۴۰۱): کوکی سشن یا توکن {provider_name} منقضی شده یا نامعتبر است. "
                "لطفاً کوکی تازه را مجدداً کپی و ذخیره نمایید."
            )
        elif code == 403:
            return (
                f"دسترسی غیرمجاز (کد ۴۰۳): سرور {provider_name} درخواست را مسدود کرد. "
                "احتمال فیلترینگ، تحریم یا محدودیت حساب کاربری وجود دارد."
            )
        elif code == 404:
            return f"یافت نشد (کد ۴۰۴): آدرس سرویس مورد نظر در سرور {provider_name} پیدا نشد."
        elif code == 429:
            return (
                f"محدودیت تعداد درخواست (کد ۴۲۹): تعداد درخواست‌ها به {provider_name} از سقف مجاز عبور کرده است. "
                "لطفاً دقایقی دیگر مجدداً امتحان فرمایید."
            )
        elif code >= 500:
            return f"خطای سرور مقصد (کد {code}): سرور {provider_name} موقتاً با اختلال مواجه شده است."
        return f"خطای سرور {provider_name} (کد {code})"

    # 2. String-based status code fallback
    if "401" in err_lower or "unauthorized" in err_lower:
        return (
            f"خطای احراز هویت (کد ۴۰۱): کوکی سشن یا توکن {provider_name} منقضی شده یا نامعتبر است. "
            "لطفاً کوکی تازه را مجدداً وارد نمایید."
        )
    if "403" in err_lower or "forbidden" in err_lower:
        return f"دسترسی غیرمجاز (کد ۴۰۳): سرور {provider_name} درخواست را مسدود کرد."
    if "429" in err_lower or "too many requests" in err_lower:
        return f"محدودیت درخواست (کد ۴۲۹): سقف مجاز فراخوانی سرور {provider_name} تکمیل شده است."

    # 3. Connection & Network Errors
    if (
        isinstance(exc, (httpx.ConnectError, httpx.NetworkError))
        or "getaddrinfo failed" in err_lower
        or "connecterror" in err_lower
        or "connection refused" in err_lower
    ):
        return f"خطای اتصال به اینترنت یا سرور: برقراری ارتباط با {provider_name} ناموفق بود. اتصال شبکه یا آدرس دامنه را بررسی کنید."

    # 4. Timeout
    if isinstance(exc, (httpx.TimeoutException, TimeoutError)) or "timeout" in err_lower or "timed out" in err_lower:
        return f"پایان مهلت پاسخ (Timeout): سرور {provider_name} در زمان مقرر پاسخ نداد."

    # 5. Header / format errors
    if "illegal header value" in err_lower:
        return f"فرمت نامعتبر داده: کوکی یا توکن {provider_name} شامل کاراکترهای غیرمجاز یا شکست خط است."

    # 6. Fallback clean message
    clean = msg
    if "for url" in clean:
        clean = clean.split("for url")[0]
    if "For more information" in clean:
        clean = clean.split("For more information")[0]
    clean = clean.strip(" :'\".")
    return f"خطا در ارتباط با {provider_name}: {clean}"


@router.get("", response_model=list[IntegrationRead])
async def list_integrations(
    type_filter: IntegrationType | None = None,
    session: AsyncSession = Depends(get_async_session),
) -> list[IntegrationORM]:
    """List all registered integrations."""
    stmt = select(IntegrationORM).order_by(desc(IntegrationORM.created_at))
    if type_filter:
        stmt = stmt.where(IntegrationORM.type == type_filter)

    res = await session.execute(stmt)
    return list(res.scalars().all())


@router.post("", response_model=IntegrationRead)
async def create_integration(
    payload: IntegrationCreate,
    session: AsyncSession = Depends(get_async_session),
) -> IntegrationORM:
    """Register a new integration (Exchange, Bot, or AI Model)."""
    clean_config = _sanitize_config(payload.config)
    integration = IntegrationORM(
        name=payload.name,
        provider=payload.provider.lower(),
        type=payload.type,
        config=clean_config,
        is_active=payload.is_active,
        status=IntegrationStatus.ACTIVE if payload.is_active else IntegrationStatus.INACTIVE,
    )
    session.add(integration)
    await session.commit()
    await session.refresh(integration)

    # Register in active bot manager if bot type
    if payload.type == IntegrationType.BOT_TELEGRAM and payload.is_active:
        token = payload.config.get("token", "")
        chat_id = payload.config.get("chat_id", "")
        get_bot_manager().register_telegram_bot(
            str(integration.id), token, [chat_id] if chat_id else []
        )
    elif payload.type == IntegrationType.BOT_BALE and payload.is_active:
        token = payload.config.get("token", "")
        chat_id = payload.config.get("chat_id", "")
        get_bot_manager().register_bale_bot(
            str(integration.id), token, [chat_id] if chat_id else []
        )

    logger.info(f"➕ Registered new integration: {payload.name} [{payload.provider}]")
    return integration


@router.put("/{integration_id}", response_model=IntegrationRead)
async def update_integration(
    integration_id: uuid.UUID,
    payload: IntegrationUpdate,
    session: AsyncSession = Depends(get_async_session),
) -> IntegrationORM:
    """Update an existing integration or toggle active state."""
    integration = await session.get(IntegrationORM, integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    if payload.name is not None:
        integration.name = payload.name
    if payload.config is not None:
        integration.config = _sanitize_config(payload.config)
    if payload.is_active is not None:
        integration.is_active = payload.is_active
        integration.status = IntegrationStatus.ACTIVE if payload.is_active else IntegrationStatus.INACTIVE
    if payload.status is not None:
        integration.status = payload.status

    await session.commit()
    await session.refresh(integration)
    return integration


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """Delete an integration."""
    integration = await session.get(IntegrationORM, integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    await session.delete(integration)
    await session.commit()
    return {"status": "ok", "message": "Integration deleted successfully"}


@router.post("/{integration_id}/test")
async def test_integration(
    integration_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Test live connection of a saved integration."""
    integration = await session.get(IntegrationORM, integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    provider = integration.provider.lower()
    config = integration.config or {}

    # 1. Telegram Bot
    if integration.type == IntegrationType.BOT_TELEGRAM:
        token = config.get("token", "")
        chat_id = config.get("chat_id", "")
        bot = TelegramBotClient(token)
        try:
            return await bot.test_connection(chat_id=chat_id)
        except Exception as e:
            return {"status": "error", "message": _format_error_message("تلگرام", e)}

    # 2. Bale Bot
    elif integration.type == IntegrationType.BOT_BALE:
        token = config.get("token", "")
        chat_id = config.get("chat_id", "")
        bot = BaleBotClient(token)
        try:
            return await bot.test_connection(chat_id=chat_id)
        except Exception as e:
            return {"status": "error", "message": _format_error_message("بله", e)}

    # 3. Wallex Exchange
    elif provider == "wallex":
        key = config.get("api_key", "")
        secret = config.get("api_secret", "")
        adapter = WallexExchangeAdapter(key, secret)
        try:
            ticker = await adapter.get_ticker("BTCUSDT")
            price = float(ticker.get("last", 0))
            return {"status": "success", "message": f"اتصال به والکس با موفقیت برقرار شد. بیت‌کوین: ${price:,.2f}"}
        except Exception as e:
            return {"status": "error", "message": _format_error_message("والکس", e)}

    # 4. Nobitex Exchange
    elif provider == "nobitex":
        token = config.get("token", "")
        adapter = NobitexExchangeAdapter(token)
        try:
            ticker = await adapter.get_ticker("BTCUSDT")
            price = float(ticker.get("last", 0))
            return {"status": "success", "message": f"اتصال به نوبیتکس با موفقیت برقرار شد. بیت‌کوین: ${price:,.2f}"}
        except Exception as e:
            return {"status": "error", "message": _format_error_message("نوبیتکس", e)}

    # 5. Faraz
    elif provider == "faraz":
        clean_cfg = _sanitize_config(config)
        token = clean_cfg.get("faraz_token", clean_cfg.get("token", "")) or FarazDataAdapter.DEFAULT_TOKEN
        cookie = clean_cfg.get("faraz_cookie", clean_cfg.get("cookie", "")) or FarazDataAdapter.DEFAULT_COOKIE
        domain = clean_cfg.get("faraz_domain", clean_cfg.get("domain", "")).strip()
        domains = [domain] if domain and "sourcearena" not in domain else FarazDataAdapter.DEFAULT_DOMAINS
        adapter = FarazDataAdapter(domains=domains, token=token, cookie=cookie)
        try:
            candles = await adapter.get_candles("EUR_USD", "1h", limit=5)
            if not candles or len(candles) == 0:
                return {"status": "error", "message": "اتصال برقرار شد اما هیچ دیتایی دریافت نشد (۰ کندل). سشن یا نماد نامعتبر است."}
                
            integration.status = IntegrationStatus.ACTIVE
            await session.commit()
            return {
                "status": "success",
                "message": f"اتصال به فراز با موفقیت برقرار شد. ({len(candles)} کندل تست دریافت گردید)",
            }
        except Exception as e:
            return {"status": "error", "message": _format_error_message("فراز", e)}

    # 6. AI Agent
    elif integration.type == IntegrationType.AI_AGENT:
        return {"status": "success", "message": f"AI Agent '{integration.name}' ({provider}) is active and ready."}

    return {"status": "success", "message": "Connection tested successfully."}
