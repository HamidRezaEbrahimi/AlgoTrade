# app/models/order.py
"""
Order Model — Exchange order with idempotency.

Tracks full order lifecycle from creation to fill/cancel.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


# ── Enums ─────────────────────────────────────
class OrderStatus(StrEnum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class OrderSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"


# ── SQLAlchemy ORM Model ──────────────────────
class OrderORM(Base):
    """Exchange order stored in PostgreSQL."""

    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    signal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("signals.id"), nullable=True
    )
    # Idempotency key — sent to exchange as clientOrderId
    client_order_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    exchange_order_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    exchange: Mapped[str] = mapped_column(
        String(20), nullable=False  # wallex, nobitex, paper
    )
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    order_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=OrderStatus.PENDING.value
    )

    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    filled: Mapped[float] = mapped_column(Float, default=0.0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    fee: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )


# ── Pydantic Schema ──────────────────────────
class Order(BaseModel):
    """Order data transfer object."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    client_order_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    exchange_order_id: str | None = None
    symbol: str
    exchange: str
    side: OrderSide
    order_type: OrderType
    status: OrderStatus = OrderStatus.PENDING
    price: float | None = None
    amount: float
    filled: float = 0.0
    cost: float = 0.0
    fee: float = 0.0
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
