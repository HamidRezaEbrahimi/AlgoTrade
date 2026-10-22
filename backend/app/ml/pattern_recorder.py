# app/ml/pattern_recorder.py
"""
Pattern Recorder, Quality Grading, and Dataset Management Service.

Provides:
- 3 Recording Modes: "auto", "manual", "disabled"
- Quality Grading: STRONG (A), NORMAL (B), WEAK (C) with 0-100 PQS score
- Lifecycle Segregation: TARGET_HIT (success), INVALIDATED (failed), ACTIVE
- Persistent Dataset Storage & Deduplication for Self-Supervised ML
"""
from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.ml.wave_scorer import FEATURE_NAMES, get_wave_scorer

logger = logging.getLogger("algotrade.ml.pattern_recorder")

DATASET_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "datasets"
RECORDER_CONFIG_PATH = DATASET_DIR / "recorder_config.json"
PATTERNS_DB_PATH = DATASET_DIR / "recorded_patterns.json"


@dataclass
class QualityGradeResult:
    """Detailed quality assessment result."""
    score: int
    grade: str  # "STRONG" | "NORMAL" | "WEAK"
    grade_color: str
    breakdown: dict[str, int]
    strengths: list[str]
    cautions: list[str]


@dataclass
class RecordedPatternItem:
    """Stored pattern record with features, labels, and quality grade."""
    id: str
    symbol: str
    timeframe: str
    name: str
    direction: str
    lifecycle_status: str  # "TARGET_HIT" | "INVALIDATED" | "ACTIVE"
    label: int | None  # 1 for TARGET_HIT, 0 for INVALIDATED, None for ACTIVE
    quality_score: int
    quality_grade: str
    grade_color: str
    features: list[float]
    feature_names: list[str]
    recorded_mode: str  # "auto" | "manual"
    recorded_at: str
    updated_at: str
    points: list[dict[str, Any]] = field(default_factory=list)
    trade_zones: dict[str, Any] = field(default_factory=dict)
    breakdown: dict[str, int] = field(default_factory=dict)


def compute_pattern_quality(
    retr_a: float = 0.618,
    retr_b: float = 1.272,
    retr_c: float = 0.85,
    slope_ratio: float = 1.25,
    er_b: float = 0.25,
    dtw_score: float = 0.05,
    rr_ratio: float = 2.0,
) -> QualityGradeResult:
    """
    Compute Pattern Quality Score (0-100) and grade (STRONG, NORMAL, WEAK).
    - Fibonacci Zone Alignment: up to 30 pts
    - Structural Cleanliness & Noise (ER & DTW): up to 30 pts
    - Momentum & Slope Ratio: up to 20 pts
    - Risk/Reward Quality: up to 20 pts
    """
    fibo_score = 0
    # Retr A (0.50 - 0.786)
    if 0.58 <= retr_a <= 0.68:
        fibo_score += 10
    elif 0.50 <= retr_a <= 0.786:
        fibo_score += 7
    else:
        fibo_score += 3

    # Retr B (1.10 - 1.382)
    if 1.20 <= retr_b <= 1.30:
        fibo_score += 10
    elif 1.05 <= retr_b <= 1.40:
        fibo_score += 7
    else:
        fibo_score += 3

    # Retr C (0.618 - 0.95)
    if 0.75 <= retr_c <= 0.90:
        fibo_score += 10
    elif 0.618 <= retr_c <= 1.0:
        fibo_score += 7
    else:
        fibo_score += 3

    # Noise & Cleanliness (ER & DTW) - up to 30 pts
    noise_score = 0
    if er_b <= 0.25:
        noise_score += 15
    elif er_b <= 0.38:
        noise_score += 10
    else:
        noise_score += 5

    if dtw_score <= 0.08:
        noise_score += 15
    elif dtw_score <= 0.15:
        noise_score += 10
    else:
        noise_score += 5

    # Slope Ratio - up to 20 pts
    slope_score = 0
    if slope_ratio >= 1.3:
        slope_score = 20
    elif slope_ratio >= 1.0:
        slope_score = 14
    else:
        slope_score = 6

    # Risk to Reward - up to 20 pts
    rr_score = 0
    if rr_ratio >= 2.5:
        rr_score = 20
    elif rr_ratio >= 2.0:
        rr_score = 16
    elif rr_ratio >= 1.5:
        rr_score = 12
    else:
        rr_score = 5

    total_score = fibo_score + noise_score + slope_score + rr_score
    total_score = min(100, max(0, total_score))

    strengths: list[str] = []
    cautions: list[str] = []

    if fibo_score >= 25:
        strengths.append("نسبت‌های فیبوناچی در محدوده زون طلایی و بهینه قرار دارد.")
    else:
        cautions.append("انحراف نسبی در ترازهای اصلاحی موج‌های A یا B.")

    if noise_score >= 25:
        strengths.append("امواج با فشردگی بالا و نویز کم بدون رانه ناگهانی شکل گرفته‌اند.")
    else:
        cautions.append("نوسانات چاپی یا واگرایی شکلی در موج اصلاحی دیده می‌شود.")

    if slope_score >= 18:
        strengths.append("شیب اصلاحی بسیار آرام‌تر از رانه قبلی است که نشانه انباشت ایده‌آل است.")
    if rr_score >= 16:
        strengths.append(f"نسبت ریسک به ریوارد بالا ({rr_ratio:.1f}) بازدهی مورد انتظار را تقویت می‌کند.")

    if total_score >= 80:
        grade = "STRONG"
        color = "#10b981"  # Emerald
    elif total_score >= 55:
        grade = "NORMAL"
        color = "#3b82f6"  # Blue
    else:
        grade = "WEAK"
        color = "#f59e0b"  # Amber

    return QualityGradeResult(
        score=total_score,
        grade=grade,
        grade_color=color,
        breakdown={
            "fibonacci": fibo_score,
            "noise_cleanliness": noise_score,
            "slope_momentum": slope_score,
            "risk_reward": rr_score,
        },
        strengths=strengths,
        cautions=cautions,
    )


class PatternRecorder:
    """Singleton service for recording patterns, grading quality, and feeding the ML pipeline."""

    def __init__(self) -> None:
        DATASET_DIR.mkdir(parents=True, exist_ok=True)
        self.config_path = RECORDER_CONFIG_PATH
        self.db_path = PATTERNS_DB_PATH
        self._mode: str = "auto"  # "auto" | "manual" | "disabled"
        self._lock = threading.Lock()
        self._load_config()

    def _load_config(self) -> None:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._mode = data.get("mode", "auto")
            except Exception as e:
                logger.warning(f"Error loading recorder config: {e}")

    def save_config(self, mode: str) -> dict[str, str]:
        if mode not in ("auto", "manual", "disabled"):
            raise ValueError(f"Invalid mode: {mode}. Must be 'auto', 'manual', or 'disabled'.")
        self._mode = mode
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump({"mode": mode, "updated_at": datetime.now(timezone.utc).isoformat()}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write recorder config: {e}")
        return {"mode": self._mode}

    def get_mode(self) -> str:
        return self._mode

    def _read_records(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            if not self.db_path.exists():
                return {}
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read patterns db: {e}")
                return {}

    def _write_records(self, records: dict[str, dict[str, Any]]) -> None:
        with self._lock:
            try:
                with open(self.db_path, "w", encoding="utf-8") as f:
                    json.dump(records, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Failed to write patterns db: {e}")

    def record_pattern(
        self,
        pattern_dict: dict[str, Any],
        symbol: str,
        timeframe: str,
        is_manual: bool = False,
    ) -> dict[str, Any] | None:
        """
        Record or update a pattern based on active mode and lifecycle.
        - If mode == 'disabled': return None
        - If mode == 'manual' and not is_manual: return None
        - Computes quality grade and feature vector.
        """
        if self._mode == "disabled":
            return None
        if self._mode == "manual" and not is_manual:
            return None

        pat_id = pattern_dict.get("id") or f"{symbol}_{timeframe}_{pattern_dict.get('name', 'wave')}_{pattern_dict.get('time', 0)}"

        # Determine lifecycle & label
        lifecycle = pattern_dict.get("lifecycle_status", "ACTIVE")
        if pattern_dict.get("is_invalidated") or lifecycle == "INVALIDATED":
            lifecycle = "INVALIDATED"
            label = 0
        elif pattern_dict.get("is_target_hit") or lifecycle == "TARGET_HIT":
            lifecycle = "TARGET_HIT"
            label = 1
        else:
            lifecycle = "ACTIVE"
            label = None

        # Extract numerical features
        retr_a = float(pattern_dict.get("retr_a", 0.618))
        retr_b = float(pattern_dict.get("retr_b", 1.272))
        retr_c = float(pattern_dict.get("retr_c", 0.85))
        slope_ratio = float(pattern_dict.get("slope_ratio", 1.25))
        er_b = float(pattern_dict.get("er_b", 0.25))
        chop_b = float(pattern_dict.get("chop_b", 45.0))
        dtw_score = float(pattern_dict.get("dtw_score", 0.05))

        # Risk reward
        rr_val = 2.0
        tz = pattern_dict.get("trade_zones")
        if tz and isinstance(tz, dict):
            entry = tz.get("entry_b", {}).get("price", 0) or tz.get("entry_a", {}).get("price", 0)
            sl = tz.get("stop_loss", {}).get("price", 0)
            tp = tz.get("tp1", {}).get("price", 0)
            if entry and sl and tp and abs(entry - sl) > 1e-6:
                rr_val = abs(tp - entry) / abs(entry - sl)
        elif "trade_setup" in pattern_dict and pattern_dict["trade_setup"]:
            rr_val = float(pattern_dict["trade_setup"].get("risk_reward_ratio", 2.0))

        # Compute Quality Grade
        qg = compute_pattern_quality(
            retr_a=retr_a,
            retr_b=retr_b,
            retr_c=retr_c,
            slope_ratio=slope_ratio,
            er_b=er_b,
            dtw_score=dtw_score,
            rr_ratio=rr_val,
        )

        features = [retr_a, retr_b, retr_c, slope_ratio, er_b, chop_b, dtw_score]

        now_str = datetime.now(timezone.utc).isoformat()
        records = self._read_records()

        existing = records.get(pat_id)
        created_at = existing.get("recorded_at", now_str) if existing else now_str

        item = RecordedPatternItem(
            id=pat_id,
            symbol=symbol,
            timeframe=timeframe,
            name=pattern_dict.get("name", "Running Flat"),
            direction=pattern_dict.get("direction", "bullish"),
            lifecycle_status=lifecycle,
            label=label,
            quality_score=qg.score,
            quality_grade=qg.grade,
            grade_color=qg.grade_color,
            features=features,
            feature_names=FEATURE_NAMES,
            recorded_mode="manual" if is_manual else "auto",
            recorded_at=created_at,
            updated_at=now_str,
            points=pattern_dict.get("points", []),
            trade_zones=pattern_dict.get("trade_zones", {}),
            breakdown=qg.breakdown,
        )

        records[pat_id] = asdict(item)
        self._write_records(records)
        logger.info(f"Recorded pattern {pat_id} (Lifecycle: {lifecycle}, Grade: {qg.grade}, Score: {qg.score})")
        return asdict(item)

    def get_recordings(
        self,
        lifecycle: str | None = None,
        grade: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Retrieve stored patterns with optional filters."""
        records = self._read_records()
        items = list(records.values())

        if lifecycle:
            items = [x for x in items if x.get("lifecycle_status") == lifecycle.upper()]
        if grade:
            items = [x for x in items if x.get("quality_grade") == grade.upper()]

        # Sort newest first
        items.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return items[:limit]

    def get_stats(self) -> dict[str, Any]:
        """Summary statistics of stored patterns."""
        records = self._read_records()
        total = len(records)
        target_hits = sum(1 for x in records.values() if x.get("lifecycle_status") == "TARGET_HIT")
        invalidated = sum(1 for x in records.values() if x.get("lifecycle_status") == "INVALIDATED")
        active = sum(1 for x in records.values() if x.get("lifecycle_status") == "ACTIVE")

        strong = sum(1 for x in records.values() if x.get("quality_grade") == "STRONG")
        normal = sum(1 for x in records.values() if x.get("quality_grade") == "NORMAL")
        weak = sum(1 for x in records.values() if x.get("quality_grade") == "WEAK")

        return {
            "mode": self._mode,
            "total_patterns": total,
            "lifecycle": {
                "target_hit": target_hits,
                "invalidated": invalidated,
                "active": active,
            },
            "grades": {
                "strong": strong,
                "normal": normal,
                "weak": weak,
            },
            "labeled_for_training": target_hits + invalidated,
        }

    def trigger_retraining(self) -> dict[str, Any]:
        """Fetch all labeled patterns and train active ML model."""
        records = self._read_records()
        labeled_samples: list[dict[str, Any]] = []

        for item in records.values():
            lbl = item.get("label")
            feat = item.get("features")
            if lbl in (0, 1) and feat and len(feat) == len(FEATURE_NAMES):
                labeled_samples.append({"features": feat, "label": lbl})

        scorer = get_wave_scorer()
        return scorer.train_model(labeled_samples)


_RECORDER: PatternRecorder | None = None


def get_pattern_recorder() -> PatternRecorder:
    global _RECORDER
    if _RECORDER is None:
        _RECORDER = PatternRecorder()
    return _RECORDER
