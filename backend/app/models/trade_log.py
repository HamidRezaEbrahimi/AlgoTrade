# app/models/trade_log.py
"""
Trade Log Model — Completed trade record.

Captures entry/exit reasons, actual R:R, PnL, and hold duration.
Used for performance reporting (Win Rate, PF, MDD, Expectancy).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from pydantic import BaseModel, Field
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Interval,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


# ── SQLAlchemy ORM Model ──────────────────────
class TradeLogORM(Base):
    """Completed trade record in PostgreSQL."""

    __tablename__ = "trade_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    signal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("signals.id"), nullable=True
    )
    position_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("positions.id"), nullable=True
    )

    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)

    # Entry
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    entry_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    entry_reason_code: Mapped[str] = mapped_column(String(50), nullable=False)
    entry_reason_text: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # Exit
    exit_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    exit_reason_code: Mapped[str] = mapped_column(
        String(50), nullable=False
        # STOP_LOSS, TRAILING_STOP, CHOCH_BEARISH,
        # RESISTANCE_REJECTION, TP_HIT, MANUAL, KILL_SWITCH
    )
    exit_reason_text: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # Size & Fees
    size: Mapped[float] = mapped_column(Float, nullable=False)
    total_fees: Mapped[float] = mapped_column(Float, default=0.0)

    # Performance
    pnl: Mapped[float] = mapped_column(Float, nullable=False)
    pnl_percent: Mapped[float] = mapped_column(Float, nullable=False)
    risk_reward_actual: Mapped[float] = mapped_column(Float, nullable=False)
    hold_duration: Mapped[timedelta | None] = mapped_column(
        Interval, nullable=True
    )

    # Peak excursions (for optimization)
    max_favorable_excursion: Mapped[float] = mapped_column(
        Float, default=0.0
    )
    max_adverse_excursion: Mapped[float] = mapped_column(
        Float, default=0.0
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ── Pydantic Schema ──────────────────────────
class TradeLog(BaseModel):
    """Trade log data transfer object."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    symbol: str
    exchange: str
    direction: str
    entry_price: float
    entry_time: datetime
    entry_reason_code: str
    entry_reason_text: str | None = None
    exit_price: float
    exit_time: datetime
    exit_reason_code: str
    exit_reason_text: str | None = None
    size: float
    total_fees: float = 0.0
    pnl: float
    pnl_percent: float
    risk_reward_actual: float
    hold_duration: timedelta | None = None

    model_config = {"from_attributes": True}
