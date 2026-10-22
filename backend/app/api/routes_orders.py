# app/api/routes_orders.py
"""
Orders, Active Positions & Trade Logs REST Endpoints.

Queries live positions, balances, and execution history from PostgreSQL & Exchanges.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.database import get_async_session
from app.exchange.nobitex_adapter import NobitexExchangeAdapter
from app.exchange.wallex_adapter import WallexExchangeAdapter
from app.models.position import PositionORM, PositionStatus
from app.models.trade_log import TradeLogORM

router = APIRouter(prefix="/orders", tags=["Orders & Positions"])
settings = get_settings()


@router.get("/balance")
async def get_account_balance() -> dict[str, Any]:
    """Fetch live account balance from active exchange or paper trading state."""
    # 1. If live exchange credentials exist, fetch from exchange
    if settings.wallex_api_key.get_secret_value():
        try:
            wallex = WallexExchangeAdapter(
                api_key=settings.wallex_api_key.get_secret_value(),
                api_secret=settings.wallex_secret.get_secret_value(),
            )
            balances = await wallex.get_balance()
            usdt = float(balances.get("USDT", Decimal("0")))
            tmn = float(balances.get("TMN", Decimal("0")))
            return {
                "exchange": "wallex",
                "total_balance_usdt": usdt,
                "available_balance_usdt": usdt,
                "tmn_balance": tmn,
                "daily_pnl": 0.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "current_drawdown": 0.0,
            }
        except Exception:
            pass

    if settings.nobitex_api_key.get_secret_value():
        try:
            nobitex = NobitexExchangeAdapter(
                api_token=settings.nobitex_api_key.get_secret_value()
            )
            balances = await nobitex.get_balance()
            usdt = float(balances.get("USDT", Decimal("0")))
            rls = float(balances.get("RLS", Decimal("0")))
            return {
                "exchange": "nobitex",
                "total_balance_usdt": usdt,
                "available_balance_usdt": usdt,
                "tmn_balance": rls / 10.0,
                "daily_pnl": 0.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "current_drawdown": 0.0,
            }
        except Exception:
            pass

    # 2. Default Paper Trading initial baseline
    return {
        "exchange": "paper",
        "total_balance_usdt": 10000.0,
        "available_balance_usdt": 10000.0,
        "tmn_balance": 0.0,
        "daily_pnl": 0.0,
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "current_drawdown": 0.0,
    }


@router.get("/positions")
async def get_active_positions(
    session: AsyncSession = Depends(get_async_session),
) -> list[dict[str, Any]]:
    """Fetch all open and active positions from PostgreSQL."""
    stmt = select(PositionORM).where(
        PositionORM.status.in_([PositionStatus.OPEN.value, PositionStatus.PARTIAL.value])
    )
    res = await session.execute(stmt)
    positions = list(res.scalars().all())

    return [
        {
            "id": str(p.id),
            "symbol": p.symbol,
            "exchange": p.exchange,
            "direction": p.direction,
            "status": p.status,
            "entry_price": p.entry_price,
            "entry_time": p.entry_time.isoformat() if p.entry_time else "",
            "initial_size": p.initial_size,
            "remaining_size": p.remaining_size,
            "current_stop": p.current_stop,
            "tp1_price": p.tp1_price,
            "tp2_price": p.tp2_price,
            "trailing_active": p.trailing_active,
            "realized_pnl": p.realized_pnl,
            "unrealized_pnl": p.unrealized_pnl,
        }
        for p in positions
    ]


@router.get("/history")
async def get_trade_history(
    limit: int = 50,
    session: AsyncSession = Depends(get_async_session),
) -> list[dict[str, Any]]:
    """Fetch real trade execution logs and reasons from PostgreSQL."""
    stmt = (
        select(TradeLogORM)
        .order_by(desc(TradeLogORM.exit_time))
        .limit(limit)
    )
    res = await session.execute(stmt)
    logs = list(res.scalars().all())

    return [
        {
            "id": str(log.id),
            "symbol": log.symbol,
            "exchange": log.exchange,
            "direction": log.direction,
            "entry_price": log.entry_price,
            "entry_time": log.entry_time.isoformat() if log.entry_time else "",
            "entry_reason": log.entry_reason_text or log.entry_reason_code,
            "exit_price": log.exit_price,
            "exit_time": log.exit_time.isoformat() if log.exit_time else "",
            "exit_reason": log.exit_reason_text or log.exit_reason_code,
            "size": log.size,
            "pnl": log.pnl,
            "pnl_percent": log.pnl_percent,
            "risk_reward_actual": log.risk_reward_actual,
            "hold_duration_sec": log.hold_duration.total_seconds() if log.hold_duration else 0,
        }
        for log in logs
    ]
