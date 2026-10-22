# app/strategy/base_strategy.py
"""
Abstract Strategy Protocol.

Every strategy (built-in or user-created) must implement this interface.
The backtest engine and live scanner use this protocol to evaluate signals
from any strategy source (hardcoded, YAML-driven, or ML-based).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.models.signal import Signal


@dataclass
class StrategyMetadata:
    """Descriptive metadata for a strategy."""

    key: str
    name_fa: str
    name_en: str
    description_fa: str = ""
    description_en: str = ""
    family: str = "custom"
    version: str = "1.0.0"
    is_builtin: bool = False
    author: str = "user"
    tags: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyEvalContext:
    """Input context passed to strategy evaluation."""

    symbol: str
    current_price: float
    timestamp: datetime
    # Multi-timeframe OHLCV arrays
    h4_opens: list[float] = field(default_factory=list)
    h4_highs: list[float] = field(default_factory=list)
    h4_lows: list[float] = field(default_factory=list)
    h4_closes: list[float] = field(default_factory=list)
    h4_volumes: list[float] = field(default_factory=list)
    h1_opens: list[float] = field(default_factory=list)
    h1_highs: list[float] = field(default_factory=list)
    h1_lows: list[float] = field(default_factory=list)
    h1_closes: list[float] = field(default_factory=list)
    h1_volumes: list[float] = field(default_factory=list)
    m15_opens: list[float] = field(default_factory=list)
    m15_highs: list[float] = field(default_factory=list)
    m15_lows: list[float] = field(default_factory=list)
    m15_closes: list[float] = field(default_factory=list)
    m15_volumes: list[float] = field(default_factory=list)
    # User-supplied wave points (for pattern-based strategies)
    wave_points: dict[str, float] | None = None
    # Extra context
    extra: dict[str, Any] = field(default_factory=dict)


class BaseStrategy(ABC):
    """Abstract base class for all trading strategies."""

    @abstractmethod
    def get_metadata(self) -> StrategyMetadata:
        """Return strategy identity and parameter info."""
        ...

    @abstractmethod
    def evaluate(
        self,
        ctx: StrategyEvalContext,
    ) -> Signal | None:
        """
        Evaluate strategy on current market data.

        Returns a Signal if entry conditions are met, None otherwise.
        Must only use closed-candle data (no look-ahead).
        """
        ...

    @abstractmethod
    def validate_config(self) -> list[str]:
        """
        Validate strategy configuration.

        Returns a list of error messages. Empty list means valid.
        """
        ...

    def get_required_timeframes(self) -> list[str]:
        """Return list of required timeframes (default: 4h, 1h, 15m)."""
        return ["4h", "1h", "15m"]
