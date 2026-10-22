# app/db/database.py
"""
PostgreSQL Async Database Engine & Session Factory.

Uses SQLAlchemy 2.0 async API with asyncpg driver.
Creates tables on startup; Alembic handles migrations.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

logger = logging.getLogger("algotrade.db")

settings = get_settings()

# ── Async Engine ──────────────────────────────
async_engine = create_async_engine(
    settings.db_url,
    echo=settings.log_level == "DEBUG",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# ── Session Factory ───────────────────────────
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""

    pass


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables on startup (dev convenience)."""
    # Import all models to register them on Base.metadata
    from app.models.candle import CandleORM  # noqa: F401
    from app.models.integration import IntegrationORM  # noqa: F401
    from app.models.order import OrderORM  # noqa: F401
    from app.models.position import PositionORM  # noqa: F401
    from app.models.signal import SignalORM  # noqa: F401
    from app.models.strategy_config import StrategyConfigORM  # noqa: F401
    from app.models.trade_log import TradeLogORM  # noqa: F401
    from app.models.user import UserORM  # noqa: F401

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created/verified.")
