# app/strategy/yaml_strategy.py
"""
YAML-Driven Strategy Loader & Evaluator.

Loads a strategy definition from YAML and evaluates it against
market data using the condition evaluator and feature calculator.
"""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import yaml

from app.models.signal import EntryScores, Signal
from app.strategy.base_strategy import (
    BaseStrategy,
    StrategyEvalContext,
    StrategyMetadata,
)
from app.strategy.condition_evaluator import evaluate_conditions
from app.strategy.feature_calculator import (
    compute_price_action_features,
    compute_wave_features,
)

logger = logging.getLogger("algotrade.strategy.yaml_strategy")


class YAMLStrategy(BaseStrategy):
    """Strategy loaded from a YAML definition file."""

    def __init__(
        self,
        yaml_path: str | None = None,
        yaml_content: str | None = None,
    ) -> None:
        if yaml_content:
            self._config = yaml.safe_load(yaml_content)
        elif yaml_path:
            with open(yaml_path, encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        else:
            raise ValueError("Either yaml_path or yaml_content required")

        self._strategy = self._config.get("strategy", {})
        self._meta_block = self._config.get("meta", {})
        self._params = self._config.get("parameters", {})
        self._entry_conds = self._config.get("entry_conditions", {})
        self._exit_rules = self._config.get("exit_rules", {})
        self._scenarios = self._config.get("outcome_scenarios", [])
        self._engine_mode = self._meta_block.get("engine", {}).get(
            "mode", "price_action"
        )

    def get_metadata(self) -> StrategyMetadata:
        names = self._strategy.get("names", {})
        desc = self._strategy.get("description", {})
        return StrategyMetadata(
            key=self._strategy.get("key", "unknown"),
            name_fa=names.get("fa", ""),
            name_en=names.get("en", ""),
            description_fa=desc.get("fa", "") if isinstance(desc, dict) else str(desc),
            description_en=desc.get("en", "") if isinstance(desc, dict) else "",
            family=self._strategy.get("family", "custom"),
            version=self._meta_block.get("strategy_version", "1.0.0"),
            is_builtin=self._strategy.get("is_builtin", False),
            tags=self._strategy.get("tags", []),
            parameters=self._params,
        )

    def validate_config(self) -> list[str]:
        errors: list[str] = []
        if not self._strategy.get("key"):
            errors.append("strategy.key is required")
        if not self._strategy.get("names"):
            errors.append("strategy.names (fa/en) is required")
        if not self._entry_conds:
            errors.append("entry_conditions block is required")
        if not self._scenarios:
            errors.append("At least one outcome_scenario is required")
        return errors

    def evaluate(
        self,
        ctx: StrategyEvalContext,
    ) -> Signal | None:
        """Evaluate strategy against market context."""
        # Compute features based on engine mode
        if self._engine_mode == "wave_pattern":
            return self._evaluate_wave(ctx)
        return self._evaluate_price_action(ctx)

    def _evaluate_price_action(
        self, ctx: StrategyEvalContext
    ) -> Signal | None:
        """Evaluate price-action based strategy."""
        if len(ctx.h1_closes) < 14 or len(ctx.h4_closes) < 5:
            return None

        features = compute_price_action_features(
            h4_highs=ctx.h4_highs,
            h4_lows=ctx.h4_lows,
            h4_closes=ctx.h4_closes,
            h1_opens=ctx.h1_opens,
            h1_highs=ctx.h1_highs,
            h1_lows=ctx.h1_lows,
            h1_closes=ctx.h1_closes,
            h1_volumes=ctx.h1_volumes,
            m15_closes=ctx.m15_closes,
            m15_volumes=ctx.m15_volumes,
            current_price=ctx.current_price,
        )
        context = {"direction": features.get("direction", "LONG")}

        # Check entry conditions
        if not evaluate_conditions(self._entry_conds, features, context):
            return None

        # Match scenario
        scenario = self._match_scenario(features, context)
        if not scenario:
            return None

        outcome = scenario.get("outcome", {})
        if outcome.get("confidence", 0) < 30:
            return None

        direction = features.get("direction", "LONG")
        stop_loss = features.get("risk", {}).get("stop_loss", 0.0)
        tp1 = features.get("rr", {}).get("tp1", 0.0)

        return self._build_signal(
            ctx, direction, stop_loss, tp1, outcome, features,
        )

    def _evaluate_wave(
        self, ctx: StrategyEvalContext
    ) -> Signal | None:
        """Evaluate wave-pattern based strategy."""
        if not ctx.wave_points:
            return None

        features = compute_wave_features(
            ctx.wave_points, ctx.current_price,
        )
        context = {
            "direction": (
                "LONG"
                if features.get("direction", {}).get("bullish_impulse")
                else "SHORT"
            ),
        }

        # Check entry conditions
        if not evaluate_conditions(self._entry_conds, features, context):
            return None

        # Match scenario
        scenario = self._match_scenario(features, context)
        if not scenario:
            return None

        outcome = scenario.get("outcome", {})
        if outcome.get("confidence", 0) < 30:
            return None

        direction = context["direction"]
        risk_data = features.get("risk", {})

        return self._build_signal(
            ctx,
            direction,
            risk_data.get("stop_b", 0.0),
            risk_data.get("target_b", 0.0),
            outcome,
            features,
        )

    def _match_scenario(
        self,
        features: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Find first matching scenario by priority (ascending)."""
        sorted_scenarios = sorted(
            self._scenarios, key=lambda s: s.get("priority", 999)
        )
        for sc in sorted_scenarios:
            conds = sc.get("conditions", {})
            if evaluate_conditions(conds, features, context):
                return sc
        return None

    def _build_signal(
        self,
        ctx: StrategyEvalContext,
        direction: str,
        stop_loss: float,
        tp1: float,
        outcome: dict[str, Any],
        features: dict[str, Any],
    ) -> Signal:
        """Build Signal object from matched outcome."""
        rr_val = features.get("rr", {})
        rr = rr_val.get("value", 1.5) if isinstance(rr_val, dict) else 1.5

        # Build scores from features (for compatibility)
        scores = EntryScores(
            structure=bool(features.get("structure", {}).get("valid", False) if isinstance(features.get("structure"), dict) else features.get("structure_valid", False)),
            location=bool(features.get("location", {}).get("valid", False) if isinstance(features.get("location"), dict) else False),
            pattern=bool(features.get("pattern", {}).get("confirmed", False) if isinstance(features.get("pattern"), dict) else False),
            momentum=bool(features.get("momentum", {}).get("confirmed", False) if isinstance(features.get("momentum"), dict) else False),
            rsi=bool(features.get("rsi", {}).get("confirmed", False) if isinstance(features.get("rsi"), dict) else False),
            volume=bool(features.get("volume", {}).get("confirmed", False) if isinstance(features.get("volume"), dict) else False),
            risk_reward=bool(rr_val.get("confirmed", rr >= 1.5) if isinstance(rr_val, dict) else rr >= 1.5),
            stop_valid=bool(features.get("risk", {}).get("stop_valid", True) if isinstance(features.get("risk"), dict) else True),
        )

        return Signal(
            id=uuid.uuid4(),
            symbol=ctx.symbol,
            direction=direction,
            timestamp=ctx.timestamp or datetime.now(UTC),
            scores=scores,
            entry_price=Decimal(str(round(ctx.current_price, 6))),
            stop_loss=Decimal(str(round(stop_loss, 6))),
            take_profit_1=Decimal(str(round(tp1, 6))),
            risk_reward_ratio=Decimal(str(round(rr, 2))),
            reason_code=f"YAML_{self._strategy.get('key', 'CUSTOM')}",
            reason_description=outcome.get("reason_fa", ""),
            is_executed=False,
        )
