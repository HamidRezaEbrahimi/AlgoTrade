# app/models/integration.py
"""
Integrations Data Model.

Stores configured Exchange connections, Telegram/Bale bots, and AI Agent providers.
"""
from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class IntegrationType(enum.StrEnum):
    EXCHANGE = "exchange"
    BOT_TELEGRAM = "bot_telegram"
    BOT_BALE = "bot_bale"
    BOT_DISCORD = "bot_discord"
    AI_AGENT = "ai_agent"


class IntegrationStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UNCONFIGURED = "unconfigured"


class IntegrationORM(Base):
    """PostgreSQL ORM Table for dynamic integrations."""
    __tablename__ = "integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)  # e.g. "wallex", "nobitex", "faraz", "telegram", "bale", "gemini", "openai"
    type = Column(Enum(IntegrationType), nullable=False)
    config = Column(JSON, nullable=False, default=dict)  # stores encrypted/plain config
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(Enum(IntegrationStatus), default=IntegrationStatus.ACTIVE, nullable=False)
    last_ping_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


# ── Pydantic Schemas ──────────────────────────────────────────
class IntegrationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    provider: str = Field(..., min_length=2, max_length=50)
    type: IntegrationType
    config: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class IntegrationUpdate(BaseModel):
    name: str | None = None
    config: dict[str, Any] | None = None
    is_active: bool | None = None
    status: IntegrationStatus | None = None


class IntegrationRead(BaseModel):
    id: uuid.UUID
    name: str
    provider: str
    type: IntegrationType
    config: dict[str, Any]
    is_active: bool
    status: IntegrationStatus
    last_ping_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
