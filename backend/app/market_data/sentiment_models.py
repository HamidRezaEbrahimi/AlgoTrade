# app/market_data/sentiment_models.py
"""
Pydantic models for social sentiment data.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SentimentData(BaseModel):
    """Normalized social sentiment metrics for a trading symbol."""

    symbol: str = Field(description="Trading symbol (e.g. BTC)")
    score: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="Normalized sentiment score (0–100)",
    )
    is_bullish: bool = Field(
        default=False,
        description="True if score >= 60",
    )
    is_bearish: bool = Field(
        default=False,
        description="True if score < 40",
    )
    mentions: int = Field(
        default=0,
        description="Total social media mentions",
    )
    interactions: int = Field(
        default=0,
        description="Total social interactions (likes, shares, etc.)",
    )
    galaxy_score: float = Field(
        default=50.0,
        description="LunarCrush Galaxy Score (0–100)",
    )
    alt_rank: int = Field(
        default=500,
        description="LunarCrush AltRank (lower = better)",
    )
    creators: int = Field(
        default=0,
        description="Number of unique content creators",
    )
    source: str = Field(
        default="neutral",
        description="Data source: 'lunarcrush', 'neutral' (fallback)",
    )
    raw_data: dict[str, Any] | None = Field(
        default=None,
        description="Raw API response for debugging",
    )

    @classmethod
    def neutral(cls, symbol: str) -> SentimentData:
        """Create neutral/fallback sentiment (score=50, no data)."""
        return cls(
            symbol=symbol,
            score=50.0,
            is_bullish=False,
            is_bearish=False,
            source="neutral",
        )
