# app/api/routes_ai_agent.py
"""
AI Agent Copilot REST Endpoints.

Provides chat, trade verification, sentiment, and status APIs.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.ai_agent.agent_core import get_ai_agent
from app.market_data.sentiment_feed import get_sentiment_feed

router = APIRouter(prefix="/ai", tags=["AI Copilot & Agent"])


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)
    persona: str = Field(default="smc_master")
    active_symbol: str = Field(default="BTCUSDT")
    market_context: dict[str, Any] | None = None


class AnalyzeSymbolRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT")
    timeframe: str = Field(default="1h")
    current_price: float | None = None
    score: int | None = 7


class VerifySetupRequest(BaseModel):
    """Payload for AI trade setup verification."""
    symbol: str = Field(default="BTCUSDT")
    score: int = Field(default=0, ge=0, le=8)
    direction: str = Field(default="LONG")
    current_price: float = Field(default=0.0)
    has_bos: bool = Field(default=False)
    has_fvg: bool = Field(default=False)
    stop_loss: float = Field(default=0.0)
    take_profit_1: float = Field(default=0.0)
    rr: float = Field(default=0.0)
    rsi: float = Field(default=50.0)
    volume_confirmed: bool = Field(default=False)


@router.get("/personas")
async def get_personas() -> dict[str, Any]:
    """Get list of available AI Copilot personas."""
    agent = get_ai_agent()
    return agent.PERSONAS


@router.post("/chat")
async def chat_with_agent(payload: ChatMessageRequest) -> dict[str, Any]:
    """Chat interactively with the AI Trading Assistant."""
    agent = get_ai_agent()
    return await agent.chat(
        user_message=payload.message,
        persona=payload.persona,
        active_symbol=payload.active_symbol,
        market_context=payload.market_context,
    )


@router.post("/analyze")
async def analyze_symbol(payload: AnalyzeSymbolRequest) -> dict[str, Any]:
    """Generate instant AI analytical report on a specific symbol."""
    agent = get_ai_agent()
    price = payload.current_price or 77168.0
    score = payload.score or 7
    return agent.analyst.generate_symbol_briefing(
        symbol=payload.symbol,
        current_price=price,
        timeframe=payload.timeframe,
        score=score,
        criteria_details={},
    )


@router.post("/verify-setup")
async def verify_trade_setup(
    payload: VerifySetupRequest,
) -> dict[str, Any]:
    """Verify a trade setup through AI analysis (with rule-based fallback).

    Returns approval decision, confidence score, market sentiment, and
    concise reasoning.
    """
    agent = get_ai_agent()
    setup_data = payload.model_dump()
    return await agent.verify_trade_setup(
        symbol=payload.symbol,
        setup_data=setup_data,
    )


@router.get("/sentiment/{symbol}")
async def get_sentiment(symbol: str) -> dict[str, Any]:
    """Fetch social sentiment data for a crypto symbol.

    Uses LunarCrush if configured, else returns neutral fallback.
    """
    feed = get_sentiment_feed()
    data = await feed.get_social_metrics(symbol)
    return data.model_dump(exclude={"raw_data"})


@router.get("/status")
async def get_ai_status() -> dict[str, Any]:
    """Return AI agent and sentiment feed configuration status.

    Never exposes API keys — only reports connection status.
    """
    agent = get_ai_agent()
    feed = get_sentiment_feed()

    from app.market_data.sentiment_feed import NullSentimentFeed

    return {
        "ai_agent": agent.get_status(),
        "sentiment_feed": {
            "provider": type(feed).__name__,
            "configured": not isinstance(feed, NullSentimentFeed),
        },
    }
