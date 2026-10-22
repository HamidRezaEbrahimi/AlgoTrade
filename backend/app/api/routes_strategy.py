# app/api/routes_strategy.py
"""
Strategy Configuration & Signal Inspection REST Endpoints.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.db.database import get_async_session
from app.db.repositories import SignalRepository
from app.models.user import User

router = APIRouter(prefix="/strategy", tags=["Strategy Engine"])

CONFIG_DIR = Path(__file__).parent.parent / "config"


@router.get("/config")
async def get_strategy_config() -> dict[str, Any]:
    """Retrieve full strategy parameters from YAML SSOT."""
    cfg_path = CONFIG_DIR / "strategy_defaults.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@router.get("/signals")
async def get_recent_signals(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Get list of recent signals with full 8-criteria breakdown."""
    signals = await SignalRepository.get_recent_signals(session, limit=30)
    return [
        {
            "id": str(s.id),
            "symbol": s.symbol,
            "direction": s.direction,
            "total_score": s.total_score,
            "entry_price": s.entry_price,
            "stop_loss": s.stop_loss,
            "take_profit_1": s.take_profit_1,
            "take_profit_2": s.take_profit_2,
            "risk_reward": s.risk_reward_ratio,
            "reason_code": s.reason_code,
            "reason_fa": s.reason_description,
            "timestamp": s.timestamp.isoformat(),
            "scores": {
                "structure": s.score_structure,
                "location": s.score_location,
                "pattern": s.score_pattern,
                "momentum": s.score_momentum,
                "rsi": s.score_rsi,
                "volume": s.score_volume,
                "risk_reward": s.score_risk_reward,
                "stop_valid": s.score_stop_valid,
            },
        }
        for s in signals
    ]
