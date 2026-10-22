# app/strategy/custom_patterns.py
"""
Custom Patterns Manager.

Enables traders and AI agents to create, name, save, and retrieve custom chart
patterns and candlestick combinations with persistent JSON storage.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("algotrade.strategy.custom_patterns")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
PATTERNS_FILE = DATA_DIR / "custom_patterns.json"


class CustomPattern(BaseModel):
    """Model representing a user or AI discovered custom pattern."""

    id: str
    name_fa: str
    name_en: str
    category: str = "custom"  # "candlestick", "smc", "geometric", "ai_discovered"
    description_fa: str = ""
    description_en: str = ""
    timeframe: str = "1h"
    win_rate_estimate: float = 0.0
    profit_factor_estimate: float = 0.0
    rules: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: str = ""
    is_active: bool = True


class CustomPatternManager:
    """Manages CRUD operations for custom user patterns."""

    def __init__(self) -> None:
        self._patterns: dict[str, CustomPattern] = {}
        self._ensure_storage()
        self.load_patterns()

    def _ensure_storage(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not PATTERNS_FILE.exists():
            # Seed with default initial patterns if empty
            initial_data = [
                {
                    "id": "pat_liquidity_grab_hammer",
                    "name_fa": "هانت نقدینگی + چکش ریجکشن",
                    "name_en": "Liquidity Grab + Hammer Rejection",
                    "category": "candlestick",
                    "description_fa": "جارو کردن کف ماقبل با کندل چکش پرحجم در انتهای حرکت اصلاحی.",
                    "description_en": "Sweeping previous low with high-volume hammer candle at end of correction.",
                    "timeframe": "1h",
                    "win_rate_estimate": 68.5,
                    "profit_factor_estimate": 2.4,
                    "rules": {"sweep_prev_low": True, "candle_type": "hammer", "volume_ma_ratio": 1.3},
                    "tags": ["smc", "rejection", "hammer"],
                    "created_at": "2026-08-24 12:00:00",
                    "is_active": True,
                },
                {
                    "id": "pat_fvg_momentum_marubozu",
                    "name_fa": "پرتاب ماروبوزو از FVG",
                    "name_en": "FVG Momentum Marubozu",
                    "category": "smc",
                    "description_fa": "کندل پرقدرت صعودی بدون سایه دقیقا پس از لمس گپ ارزش منصفانه.",
                    "description_en": "Strong bullish marubozu immediately after FVG touch.",
                    "timeframe": "15m",
                    "win_rate_estimate": 72.0,
                    "profit_factor_estimate": 2.8,
                    "rules": {"fvg_touched": True, "candle_type": "marubozu", "min_body_pct": 80},
                    "tags": ["fvg", "momentum", "breakout"],
                    "created_at": "2026-08-24 12:30:00",
                    "is_active": True,
                },
            ]
            with open(PATTERNS_FILE, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)

    def load_patterns(self) -> int:
        """Load all custom patterns from JSON file."""
        if not PATTERNS_FILE.exists():
            return 0
        try:
            with open(PATTERNS_FILE, encoding="utf-8") as f:
                data = json.load(f)
                self._patterns = {item["id"]: CustomPattern(**item) for item in data}
            logger.info("Loaded %d custom patterns from %s", len(self._patterns), PATTERNS_FILE)
            return len(self._patterns)
        except Exception as e:
            logger.error("Failed to load custom patterns: %s", e)
            return 0

    def save_patterns_to_disk(self) -> None:
        """Save current in-memory patterns to JSON file."""
        try:
            data = [p.dict() for p in self._patterns.values()]
            with open(PATTERNS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("Saved %d custom patterns to %s", len(data), PATTERNS_FILE)
        except Exception as e:
            logger.error("Failed to save custom patterns: %s", e)

    def list_all(self) -> list[CustomPattern]:
        """List all custom patterns."""
        return list(self._patterns.values())

    def get(self, pattern_id: str) -> CustomPattern | None:
        """Get pattern by ID."""
        return self._patterns.get(pattern_id)

    def save_pattern(self, pattern: CustomPattern) -> CustomPattern:
        """Add or update a custom pattern."""
        self._patterns[pattern.id] = pattern
        self.save_patterns_to_disk()
        return pattern

    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete pattern by ID."""
        if pattern_id in self._patterns:
            del self._patterns[pattern_id]
            self.save_patterns_to_disk()
            return True
        return False


_instance: CustomPatternManager | None = None


def get_custom_pattern_manager() -> CustomPatternManager:
    global _instance
    if _instance is None:
        _instance = CustomPatternManager()
    return _instance
