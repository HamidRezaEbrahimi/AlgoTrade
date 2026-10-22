# app/models/user.py
"""
User Model — Multi-user authentication.

ORM model for PostgreSQL + Pydantic schemas for API.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


# ── SQLAlchemy ORM Model ──────────────────────
class User(Base):
    """User account stored in PostgreSQL."""

    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
    default_locale: Mapped[str] = mapped_column(
        String(5), default="fa"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )


UserORM = User


# ── Pydantic Schemas ──────────────────────────
class UserCreate(BaseModel):
    """Schema for user registration."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
    """Schema for user API responses (no password)."""

    id: uuid.UUID
    username: str
    email: str
    is_active: bool
    is_admin: bool
    default_locale: str
    created_at: datetime

    model_config = {"from_attributes": True}
