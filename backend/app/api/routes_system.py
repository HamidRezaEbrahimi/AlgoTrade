# app/api/routes_system.py
"""
System Health, Kill-Switch & Authentication Endpoints.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from app.config import get_settings
from app.db.database import get_async_session
from app.db.repositories import UserRepository
from app.models.user import User, UserCreate, UserResponse
from app.risk.kill_switch import KillSwitchManager, KillSwitchReport

router = APIRouter(tags=["System & Auth"])
settings = get_settings()


# ── Authentication ────────────────────────────
@router.post("/auth/register", response_model=UserResponse)
async def register_user(
    req: UserCreate,
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Register a new user account."""
    existing = await UserRepository.get_by_username(session, req.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="نام کاربری قبلاً ثبت شده است.",
        )
    user = User(
        username=req.username,
        email=req.email,
        hashed_password=get_password_hash(req.password),
        is_active=True,
    )
    return await UserRepository.create(session, user)


@router.post("/auth/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """Obtain JWT access token for authentication."""
    user = await UserRepository.get_by_username(session, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور اشتباه است.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


# ── System & Health ───────────────────────────
@router.get("/system/health")
async def get_system_health() -> dict[str, Any]:
    """System heartbeat and environment status."""
    return {
        "status": "healthy",
        "trading_mode": settings.trading_mode.value,
        "kill_switch_active": KillSwitchManager.is_active(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


# ── Kill Switch (Rule #1) ─────────────────────
@router.post("/system/kill-switch")
async def trigger_emergency_kill_switch(
    current_user: User = Depends(get_current_user),
) -> KillSwitchReport:
    """
    Emergency Kill-Switch: Immediately cancels all open orders and stops trading.
    """
    # Trigger across adapters
    report = await KillSwitchManager.trigger(
        exchange_adapters=[],
        open_positions=[],
        user_id=str(current_user.id),
        close_positions=True,
    )
    return report


@router.post("/system/kill-switch/reset")
async def reset_kill_switch(
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Reset Kill-Switch state to resume trading."""
    KillSwitchManager.reset()
    return {"message": "کلید قطع اضطراری بازنشانی شد. سامانه آماده فعالیت مجدد است."}
