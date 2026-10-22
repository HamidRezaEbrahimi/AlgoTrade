# app/config/settings.py
"""
Centralized Settings — Pydantic BaseSettings SSOT.

All configuration loaded from environment variables (.env).
Validated at startup; crashes fast on missing required values.
"""
from __future__ import annotations

import json
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TradingMode(StrEnum):
    """Execution environment isolation."""

    PAPER_TRADING = "PAPER_TRADING"
    LIVE_TRADING = "LIVE_TRADING"
    BACKTEST = "BACKTEST"


class Settings(BaseSettings):
    """Application-wide settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", str(Path(__file__).parents[3] / ".env")),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Trading Mode ──────────────────────────
    trading_mode: TradingMode = TradingMode.PAPER_TRADING

    # ── Exchange: Wallex ──────────────────────
    wallex_api_key: SecretStr = SecretStr("")
    wallex_secret: SecretStr = SecretStr("")

    # ── Exchange: Nobitex ─────────────────────
    nobitex_api_key: SecretStr = SecretStr("")
    nobitex_secret: SecretStr = SecretStr("")

    # ── Faraz API (Forex / TSE Data) ──────────
    faraz_api_domain_1: str = "https://ir4.faraz.io"
    faraz_api_domain_2: str = "https://ir3.faraz.io"
    faraz_api_domain_3: str = "https://ir2.faraz.io"
    faraz_api_token: SecretStr = SecretStr("")
    faraz_cookie: SecretStr = SecretStr("")

    # ── Database (PostgreSQL) ─────────────────
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "algotrade"
    db_user: str = "algotrade"
    db_password: SecretStr = SecretStr("changeme")

    @property
    def db_url(self) -> str:
        """Build async PostgreSQL connection URL."""
        pwd = self.db_password.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.db_user}:{pwd}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def db_url_sync(self) -> str:
        """Build sync PostgreSQL URL (for Alembic migrations)."""
        pwd = self.db_password.get_secret_value()
        return (
            f"postgresql://{self.db_user}:{pwd}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # ── Redis ─────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── API Server ────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: Any = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    # ── Authentication ────────────────────────
    jwt_secret_key: SecretStr = SecretStr("change-this-in-production")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # ── Telegram Bot ──────────────────────────
    telegram_bot_token: SecretStr = SecretStr("")
    telegram_chat_ids: Any = Field(default_factory=list)

    # ── Bale Bot ──────────────────────────────
    bale_bot_token: SecretStr = SecretStr("")
    bale_chat_ids: Any = Field(default_factory=list)

    @field_validator("cors_origins", "telegram_chat_ids", "bale_chat_ids", mode="before")
    @classmethod
    def parse_str_list(cls, val: Any) -> list[str]:
        if val is None or val == "":
            return []
        if isinstance(val, (int, float)):
            return [str(val)]
        if isinstance(val, str):
            val = val.strip()
            if val.startswith("[") and val.endswith("]"):
                try:
                    return json.loads(val)
                except Exception:
                    pass
            return [x.strip() for x in val.split(",") if x.strip()]
        if isinstance(val, (list, tuple, set)):
            return [str(x) for x in val]
        return []

    # ── Logging ───────────────────────────────
    log_level: str = "INFO"
    log_dir: Path = Path("./logs")

    # ── Language ──────────────────────────────
    default_locale: str = "fa"

    # ── Encryption ────────────────────────────
    encryption_key: SecretStr = SecretStr("")

    # ── AI Agent (LLM) ───────────────────────
    gemini_api_key: SecretStr = SecretStr("")
    gemini_model_name: str = "gemini-2.5-flash-lite"
    ai_request_timeout_seconds: int = 30

    # ── Social Sentiment ─────────────────────
    sentiment_provider: str = "lunarcrush"
    lunarcrush_api_key: SecretStr = SecretStr("")
    sentiment_cache_ttl_minutes: int = 15

    # ── Pattern & Dataset Paths (SSOT) ────────
    pattern_config_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "config" / "patterns"
    )
    ml_patterns_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "data" / "datasets" / "ml_patterns"
    )
    pattern_rules_file: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "data" / "pattern_rules.yaml"
    )

    # ── Faraz domains as list ─────────────────
    @property
    def faraz_domains(self) -> list[str]:
        """Get all configured Faraz API domains."""
        return [
            self.faraz_api_domain_1,
            self.faraz_api_domain_2,
            self.faraz_api_domain_3,
        ]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — loads once from .env."""
    return Settings()
