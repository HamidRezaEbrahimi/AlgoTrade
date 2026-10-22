# app/api/routes_strategies.py
"""
Strategy Management API Routes.

CRUD for strategies + validate + backtest with dynamic strategy.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.models.strategy_config import (
    StrategyConfigCreate,
    StrategyListItem,
)
from app.strategy.strategy_registry import get_strategy_registry
from app.strategy.yaml_strategy import YAMLStrategy

logger = logging.getLogger("algotrade.api.strategies")
router = APIRouter(prefix="/api/strategies", tags=["strategies"])


@router.get("", response_model=list[StrategyListItem])
async def list_strategies():
    """List all available strategies (built-in + custom)."""
    registry = get_strategy_registry()
    items = []
    for meta in registry.list_all():
        items.append(
            StrategyListItem(
                key=meta.key,
                name_fa=meta.name_fa,
                name_en=meta.name_en,
                family=meta.family,
                is_builtin=meta.is_builtin,
                is_active=True,
                tags=meta.tags,
            )
        )
    return items


@router.get("/{strategy_key}")
async def get_strategy(strategy_key: str):
    """Get strategy details by key."""
    registry = get_strategy_registry()
    meta = registry.get_metadata(strategy_key)
    if not meta:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {
        "key": meta.key,
        "name_fa": meta.name_fa,
        "name_en": meta.name_en,
        "family": meta.family,
        "version": meta.version,
        "is_builtin": meta.is_builtin,
        "tags": meta.tags,
        "parameters": meta.parameters,
        "description_fa": meta.description_fa,
        "description_en": meta.description_en,
    }


@router.post("")
async def create_strategy(body: StrategyConfigCreate):
    """Create a new custom strategy from YAML."""
    registry = get_strategy_registry()
    try:
        meta = registry.register_from_yaml(body.yaml_content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        "success": True,
        "key": meta.key,
        "name_fa": meta.name_fa,
        "message_fa": f"استراتژی «{meta.name_fa}» با موفقیت ایجاد شد.",
    }


@router.put("/{strategy_key}")
async def update_strategy(strategy_key: str, body: StrategyConfigCreate):
    """Update an existing custom strategy."""
    registry = get_strategy_registry()
    existing = registry.get_metadata(strategy_key)
    if not existing:
        raise HTTPException(status_code=404, detail="Strategy not found")
    if existing.is_builtin:
        raise HTTPException(
            status_code=403,
            detail="Cannot modify built-in strategies",
        )
    try:
        meta = registry.register_from_yaml(body.yaml_content, overwrite=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        "success": True,
        "key": meta.key,
        "message_fa": f"استراتژی «{meta.name_fa}» به‌روزرسانی شد.",
    }


@router.delete("/{strategy_key}")
async def delete_strategy(strategy_key: str):
    """Delete a custom strategy."""
    registry = get_strategy_registry()
    try:
        removed = registry.remove(strategy_key)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    if not removed:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {
        "success": True,
        "message_fa": f"استراتژی «{strategy_key}» حذف شد.",
    }


@router.post("/{strategy_key}/validate")
async def validate_strategy(strategy_key: str):
    """Validate a strategy configuration."""
    registry = get_strategy_registry()
    strategy = registry.get(strategy_key)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    errors = strategy.validate_config()
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "message_fa": (
            "✅ استراتژی معتبر است."
            if not errors
            else f"❌ {len(errors)} خطا یافت شد."
        ),
    }


@router.post("/validate-yaml")
async def validate_yaml_content(body: StrategyConfigCreate):
    """Validate raw YAML content without registering."""
    try:
        strategy = YAMLStrategy(yaml_content=body.yaml_content)
        errors = strategy.validate_config()
        meta = strategy.get_metadata()
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strategy_key": meta.key,
            "name_fa": meta.name_fa,
            "message_fa": (
                f"✅ YAML معتبر: «{meta.name_fa}»"
                if not errors
                else f"❌ {len(errors)} خطا"
            ),
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [str(e)],
            "message_fa": f"❌ خطا در تجزیه YAML: {e}",
        }
