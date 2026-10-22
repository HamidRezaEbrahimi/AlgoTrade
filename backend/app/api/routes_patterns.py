# app/api/routes_patterns.py
"""
Pattern Recording, Quality Grading, and Dataset Management REST Endpoints.

Enables:
- Dynamic Recorder Mode switching: auto | manual | disabled
- Manual pattern recording from Trading UI
- Querying recorded patterns by category (TARGET_HIT, INVALIDATED, ACTIVE) and grade (STRONG, NORMAL, WEAK)
- Training triggers for local self-supervised ML models
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.ml.pattern_recorder import compute_pattern_quality, get_pattern_recorder

logger = logging.getLogger("algotrade.api.patterns")

router = APIRouter(prefix="/patterns", tags=["Pattern Recorder & ML"])


class ModeUpdateRequest(BaseModel):
    mode: str = Field(..., description="One of: 'auto', 'manual', 'disabled'")


class RecordPatternRequest(BaseModel):
    pattern: dict[str, Any] = Field(..., description="Full pattern marker dictionary")
    symbol: str = Field(..., description="Ticker symbol e.g. BTCUSDT, EURUSD")
    timeframe: str = Field(..., description="Timeframe e.g. 15m, 1h, 4h")


class QualityEvaluateRequest(BaseModel):
    retr_a: float = 0.618
    retr_b: float = 1.272
    retr_c: float = 0.85
    slope_ratio: float = 1.25
    er_b: float = 0.25
    dtw_score: float = 0.05
    rr_ratio: float = 2.0


@router.get("/recorder/config")
async def get_recorder_config() -> dict[str, Any]:
    """Get current pattern recorder mode and dataset statistics."""
    recorder = get_pattern_recorder()
    stats = recorder.get_stats()
    return {
        "mode": recorder.get_mode(),
        "stats": stats,
    }


@router.post("/recorder/config")
async def set_recorder_config(payload: ModeUpdateRequest) -> dict[str, Any]:
    """Change pattern recording mode ('auto', 'manual', 'disabled')."""
    recorder = get_pattern_recorder()
    try:
        res = recorder.save_config(payload.mode.lower())
        return {"status": "ok", "mode": res["mode"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/record")
async def record_pattern_manually(payload: RecordPatternRequest) -> dict[str, Any]:
    """Manually record a pattern from the chart into the ML dataset."""
    recorder = get_pattern_recorder()
    mode = recorder.get_mode()
    if mode == "disabled":
        raise HTTPException(
            status_code=400,
            detail="Pattern recorder is currently DISABLED. Please switch to manual or auto mode first.",
        )

    item = recorder.record_pattern(
        pattern_dict=payload.pattern,
        symbol=payload.symbol,
        timeframe=payload.timeframe,
        is_manual=True,
    )
    if not item:
        raise HTTPException(status_code=400, detail="Failed to record pattern.")
    return {
        "status": "success",
        "message": "الگو با موفقیت در بانک داده‌های یادگیری ماشین ثبت گردید.",
        "item": item,
    }


@router.get("/recordings")
async def list_recorded_patterns(
    lifecycle: str | None = Query(None, description="TARGET_HIT, INVALIDATED, ACTIVE"),
    grade: str | None = Query(None, description="STRONG, NORMAL, WEAK"),
    limit: int = Query(100, ge=1, le=500),
) -> dict[str, Any]:
    """List recorded patterns filtered by outcome or quality grade."""
    recorder = get_pattern_recorder()
    items = recorder.get_recordings(lifecycle=lifecycle, grade=grade, limit=limit)
    return {
        "count": len(items),
        "patterns": items,
        "filters": {"lifecycle": lifecycle, "grade": grade},
    }


@router.post("/evaluate-quality")
async def evaluate_pattern_quality(payload: QualityEvaluateRequest) -> dict[str, Any]:
    """Evaluate pattern quality score (PQS) and return strengths and cautions."""
    res = compute_pattern_quality(
        retr_a=payload.retr_a,
        retr_b=payload.retr_b,
        retr_c=payload.retr_c,
        slope_ratio=payload.slope_ratio,
        er_b=payload.er_b,
        dtw_score=payload.dtw_score,
        rr_ratio=payload.rr_ratio,
    )
    return {
        "quality_score": res.score,
        "quality_grade": res.grade,
        "grade_color": res.grade_color,
        "breakdown": res.breakdown,
        "strengths": res.strengths,
        "cautions": res.cautions,
    }


@router.post("/train")
async def trigger_model_training() -> dict[str, Any]:
    """Trigger local training of the Tabular ML Scorer using labeled patterns."""
    recorder = get_pattern_recorder()
    try:
        result = recorder.trigger_retraining()
        return result
    except Exception as e:
        logger.error(f"Error training wave ML model: {e}")
        raise HTTPException(status_code=400, detail=str(e))
