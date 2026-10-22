# app/models/candle.py
"""
Candle (OHLCV) Model.

ORM model for time-series candle storage + Pydantic schema.
All prices stored as float for performance; Decimal used at API boundary.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import (
    DateTime,
    Float,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


# ── SQLAlchemy ORM Model ──────────────────────
class CandleORM(Base):
    """OHLCV candle stored in PostgreSQL."""

    __tablename__ = "candles"
    __table_args__ = (
        UniqueConstraint(
            "symbol", "timeframe", "timestamp",
            name="uq_candle_symbol_tf_ts",
        ),
        Index("ix_candle_symbol_tf", "symbol", "timeframe"),
        Index("ix_candle_timestamp", "timestamp"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    symbol: Mapped[str] = mapped_column(
        String(30), nullable=False
    )
    timeframe: Mapped[str] = mapped_column(
        String(10), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ── Pydantic Schema ──────────────────────────
class Candle(BaseModel):
    """Candle data transfer object."""

    symbol: str
    timeframe: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal = Decimal("0")

    model_config = {"from_attributes": True}
