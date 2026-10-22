# app/models/signal.py
"""
Signal Model — 8-Criteria Entry Signal.

Captures the full scoring breakdown for every trade opportunity.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


# ── Pydantic: Score Breakdown ─────────────────
class EntryScores(BaseModel):
    """8-criteria scoring breakdown."""

    structure: bool = False       # 1. Proper structure (4H)
    location: bool = False        # 2. Valid location (S/R, OB, FVG)
    pattern: bool = False         # 3. Entry pattern (1H)
    momentum: bool = False        # 4. Momentum (15M)
    rsi: bool = False             # 5. RSI(14) confirm
    volume: bool = False          # 6. Volume > MA(10)
    risk_reward: bool = False     # 7. RR ≥ 1.5
    stop_valid: bool = False      # 8. Valid Stop Loss

    @property
    def total(self) -> int:
        """Count of True criteria."""
        return sum([
            self.structure, self.location, self.pattern,
            self.momentum, self.rsi, self.volume,
            self.risk_reward, self.stop_valid,
        ])

    @property
    def is_valid(self) -> bool:
        """Check minimum 6/8 score."""
        return self.total >= 6


# ── SQLAlchemy ORM Model ──────────────────────
class SignalORM(Base):
    """Entry signal stored in PostgreSQL."""

    __tablename__ = "signals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    direction: Mapped[str] = mapped_column(
        String(10), nullable=False  # LONG or SHORT
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # 8 Criteria Scores
    score_structure: Mapped[bool] = mapped_column(Boolean, default=False)
    score_location: Mapped[bool] = mapped_column(Boolean, default=False)
    score_pattern: Mapped[bool] = mapped_column(Boolean, default=False)
    score_momentum: Mapped[bool] = mapped_column(Boolean, default=False)
    score_rsi: Mapped[bool] = mapped_column(Boolean, default=False)
    score_volume: Mapped[bool] = mapped_column(Boolean, default=False)
    score_risk_reward: Mapped[bool] = mapped_column(Boolean, default=False)
    score_stop_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    total_score: Mapped[int] = mapped_column(Integer, default=0)

    # Price levels
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    stop_loss: Mapped[float] = mapped_column(Float, nullable=False)
    take_profit_1: Mapped[float] = mapped_column(Float, nullable=False)
    take_profit_2: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_reward_ratio: Mapped[float] = mapped_column(Float, nullable=False)

    # Reason
    reason_code: Mapped[str] = mapped_column(String(50), nullable=False)
    reason_description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # Status
    is_executed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ── Pydantic Schema ──────────────────────────
class Signal(BaseModel):
    """Signal data transfer object."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    symbol: str
    direction: Literal["LONG", "SHORT"]
    timestamp: datetime
    scores: EntryScores
    entry_price: Decimal
    stop_loss: Decimal
    take_profit_1: Decimal
    take_profit_2: Decimal | None = None
    risk_reward_ratio: Decimal
    reason_code: str
    reason_description: str | None = None
    is_executed: bool = False

    model_config = {"from_attributes": True}
