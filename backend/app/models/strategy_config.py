# app/models/strategy_config.py
"""
Strategy Configuration — Database model for user-created strategies.

Stores YAML content and metadata for custom strategies.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


# ── SQLAlchemy ORM Model ──────────────────────
class StrategyConfigORM(Base):
    """User-created strategy stored in PostgreSQL."""

    __tablename__ = "strategy_configs"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    strategy_key: Mapped[str] = mapped_column(
        String(80), unique=True, nullable=False
    )
    name_fa: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str] = mapped_column(
        String(200), nullable=False, default=""
    )
    description_fa: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    yaml_content: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


# ── Pydantic Schemas ──────────────────────────
class StrategyConfigCreate(BaseModel):
    """Request schema for creating a strategy."""

    name_fa: str
    name_en: str = ""
    description_fa: str = ""
    yaml_content: str

    model_config = {"from_attributes": True}


class StrategyConfigUpdate(BaseModel):
    """Request schema for updating a strategy."""

    name_fa: str | None = None
    name_en: str | None = None
    description_fa: str | None = None
    yaml_content: str | None = None
    is_active: bool | None = None


class StrategyConfigResponse(BaseModel):
    """Response schema for strategy details."""

    id: uuid.UUID
    strategy_key: str
    name_fa: str
    name_en: str
    description_fa: str | None = None
    is_active: bool
    is_builtin: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StrategyListItem(BaseModel):
    """Compact strategy item for list views."""

    key: str
    name_fa: str
    name_en: str
    family: str = "custom"
    is_builtin: bool = False
    is_active: bool = True
    tags: list = Field(default_factory=list)
