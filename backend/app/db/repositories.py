# app/db/repositories.py
"""
Database Repositories — Async CRUD operations.

Encapsulates all direct SQLAlchemy session queries.
"""
from __future__ import annotations

import uuid

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.position import PositionORM, PositionStatus
from app.models.signal import SignalORM
from app.models.trade_log import TradeLogORM
from app.models.user import User


class UserRepository:
    """User accounts repository."""

    @staticmethod
    async def get_by_username(session: AsyncSession, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, user: User) -> User:
        session.add(user)
        await session.flush()
        return user


class PositionRepository:
    """Trading positions repository."""

    @staticmethod
    async def get_active_positions(session: AsyncSession, user_id: uuid.UUID) -> list[PositionORM]:
        stmt = select(PositionORM).where(
            PositionORM.user_id == user_id,
            PositionORM.status.in_([PositionStatus.OPEN.value, PositionStatus.PARTIAL.value]),
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def create(session: AsyncSession, pos: PositionORM) -> PositionORM:
        session.add(pos)
        await session.flush()
        return pos

    @staticmethod
    async def update_status(session: AsyncSession, pos_id: uuid.UUID, status: PositionStatus) -> None:
        stmt = update(PositionORM).where(PositionORM.id == pos_id).values(status=status.value)
        await session.execute(stmt)


class TradeLogRepository:
    """Completed trade logs repository."""

    @staticmethod
    async def get_user_logs(session: AsyncSession, user_id: uuid.UUID, limit: int = 50) -> list[TradeLogORM]:
        stmt = (
            select(TradeLogORM)
            .where(TradeLogORM.user_id == user_id)
            .order_by(desc(TradeLogORM.exit_time))
            .limit(limit)
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def create(session: AsyncSession, log: TradeLogORM) -> TradeLogORM:
        session.add(log)
        await session.flush()
        return log


class SignalRepository:
    """Signals repository."""

    @staticmethod
    async def create(session: AsyncSession, sig: SignalORM) -> SignalORM:
        session.add(sig)
        await session.flush()
        return sig

    @staticmethod
    async def get_recent_signals(session: AsyncSession, limit: int = 30) -> list[SignalORM]:
        stmt = select(SignalORM).order_by(desc(SignalORM.timestamp)).limit(limit)
        res = await session.execute(stmt)
        return list(res.scalars().all())
