# app/models/position.py
"""
Position Model — Active and closed positions.

Tracks entry, current stop, trailing, partial closes, and PnL.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class PositionStatus(StrEnum):
    OPEN = "OPEN"
    PARTIAL = "PARTIAL"       # After 50% close at RR=2.5
    CLOSED = "CLOSED"


# ── SQLAlchemy ORM Model ──────────────────────
class PositionORM(Base):
    """Trading position stored in PostgreSQL."""

    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    signal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("signals.id"), nullable=True
    )

    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(
        String(10), nullable=False  # LONG or SHORT
    )
    status: Mapped[str] = mapped_column(
        String(20), default=PositionStatus.OPEN.value
    )

    # Entry
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    entry_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Size management
    initial_size: Mapped[float] = mapped_column(Float, nullable=False)
    remaining_size: Mapped[float] = mapped_column(Float, nullable=False)

    # Stop Loss & Trailing
    initial_stop: Mapped[float] = mapped_column(Float, nullable=False)
    current_stop: Mapped[float] = mapped_column(Float, nullable=False)
    trailing_active: Mapped[bool] = mapped_column(Boolean, default=False)
    trailing_distance: Mapped[float | None] = mapped_column(
        Float, nullable=True  # 1.2 × ATR
    )

    # Take Profit targets
    tp1_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    tp2_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    tp1_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    tp2_hit: Mapped[bool] = mapped_column(Boolean, default=False)

    # PnL tracking
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    max_favorable: Mapped[float] = mapped_column(Float, default=0.0)
    max_adverse: Mapped[float] = mapped_column(Float, default=0.0)

    # Timestamps
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )


# ── Pydantic Schema ──────────────────────────
class Position(BaseModel):
    """Position data transfer object."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    symbol: str
    exchange: str
    direction: str
    status: PositionStatus = PositionStatus.OPEN
    entry_price: float
    entry_time: datetime
    initial_size: float
    remaining_size: float
    initial_stop: float
    current_stop: float
    trailing_active: bool = False
    trailing_distance: float | None = None
    tp1_price: float | None = None
    tp2_price: float | None = None
    tp1_hit: bool = False
    tp2_hit: bool = False
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0

    model_config = {"from_attributes": True}
