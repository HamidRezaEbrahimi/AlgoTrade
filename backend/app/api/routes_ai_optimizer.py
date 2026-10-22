# app/api/routes_ai_optimizer.py
"""
AI Optimizer, Pattern Discovery & Local Model API Routes.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai_optimizer import (
    get_local_model_engine,
    get_pattern_miner,
    get_strategy_optimizer,
)
from app.strategy.custom_patterns import CustomPattern, get_custom_pattern_manager
from app.strategy.custom_strategy_manager import get_custom_strategy_manager

logger = logging.getLogger("algotrade.api.ai_optimizer")
router = APIRouter(prefix="/api/ai-optimizer", tags=["ai_optimizer"])


class MinePatternsRequest(BaseModel):
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    min_samples: int = 15


class OptimizeStrategyRequest(BaseModel):
    strategy_key: str = "ict_silver_bullet_pm"
    target_metric: str = "sharpe_ratio"
    current_config: dict[str, Any] = Field(default_factory=dict)


class TrainModelRequest(BaseModel):
    epochs: int = 20
    learning_rate: float = 0.01
    samples_count: int = 250


class SaveCustomStrategyRequest(BaseModel):
    name: str
    key: str
    structure_tf: str = "4h"
    entry_tf: str = "1h"
    filter_tf: str = "15m"
    patterns: dict[str, bool] = Field(default_factory=dict)
    candlesticks: dict[str, bool] = Field(default_factory=dict)
    indicators: dict[str, Any] = Field(default_factory=dict)
    ai_confirmation_required: bool = False
    risk: dict[str, Any] = Field(default_factory=dict)


@router.get("/custom-patterns", response_model=list[CustomPattern])
async def list_custom_patterns():
    """List all user and AI saved custom patterns."""
    mgr = get_custom_pattern_manager()
    return mgr.list_all()


@router.post("/custom-patterns", response_model=CustomPattern)
async def save_custom_pattern(pattern: CustomPattern):
    """Save or update a custom pattern."""
    mgr = get_custom_pattern_manager()
    return mgr.save_pattern(pattern)


@router.delete("/custom-patterns/{pattern_id}")
async def delete_custom_pattern(pattern_id: str):
    """Delete a custom pattern by ID."""
    mgr = get_custom_pattern_manager()
    deleted = mgr.delete_pattern(pattern_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return {"success": True, "message_fa": "الگوی سفارشی با موفقیت حذف شد."}


@router.post("/mine-patterns")
async def mine_patterns(body: MinePatternsRequest):
    """Discover high-winrate price action patterns from market candle stream."""
    try:
        from app.market_data.market_streamer import get_market_streamer
        streamer = get_market_streamer()
        candles = streamer.get_candles(body.symbol, body.timeframe, limit=200)
    except Exception:
        candles = []
    miner = get_pattern_miner()
    discoveries = miner.mine_patterns(
        candles=candles,
        symbol=body.symbol,
        timeframe=body.timeframe,
        min_samples=body.min_samples,
    )
    return {
        "success": True,
        "symbol": body.symbol,
        "timeframe": body.timeframe,
        "total_discovered": len(discoveries),
        "patterns": discoveries,
    }


@router.post("/optimize-strategy")
async def optimize_strategy(body: OptimizeStrategyRequest):
    """Optimize strategy hyperparameters for maximum risk-adjusted return."""
    opt = get_strategy_optimizer()
    res = opt.optimize_strategy(
        strategy_key=body.strategy_key,
        current_config=body.current_config,
        target_metric=body.target_metric,
    )
    return res


@router.get("/local-model-status")
async def get_local_model_status(ollama_endpoint: str = "http://localhost:11434"):
    """Get status of local ML model and Ollama LLM."""
    engine = get_local_model_engine()
    await engine.check_ollama_connection(ollama_endpoint)
    return engine.status.to_dict()


@router.post("/train-local-model")
async def train_local_model(body: TrainModelRequest):
    """Train/Fine-tune local ML model on closed trades history."""
    engine = get_local_model_engine()
    res = engine.train_on_history(
        epochs=body.epochs,
        learning_rate=body.learning_rate,
        samples_count=body.samples_count,
    )
    return res


@router.post("/custom-strategy")
async def save_custom_strategy(body: SaveCustomStrategyRequest):
    """Save custom strategy from visual builder payload into YAML and register."""
    mgr = get_custom_strategy_manager()
    try:
        key = mgr.save_custom_strategy(body.dict())
        return {
            "success": True,
            "key": key,
            "message_fa": f"استراتژی «{body.name}» با موفقیت در دیسک ذخیره و در ریجستری فعال شد.",
        }
    except Exception as e:
        logger.error("Failed to save custom strategy: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
