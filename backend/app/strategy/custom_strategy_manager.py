# app/strategy/custom_strategy_manager.py
"""
Custom Strategy Manager & YAML Serializer.

Translates visual builder JSON payloads into institutional standard YAML files
and handles disk persistence in the strategies directory.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from app.strategy.strategy_registry import get_strategy_registry

logger = logging.getLogger("algotrade.strategy.custom_manager")

STRATEGIES_DIR = Path(__file__).resolve().parent / "strategies"


class CustomStrategyManager:
    """Handles saving, serializing, and deleting custom strategy YAML files."""

    @staticmethod
    def json_to_yaml_content(payload: dict[str, Any]) -> str:
        """Convert a visual builder JSON dictionary into standard strategy YAML."""
        name_fa = payload.get("name") or payload.get("name_fa") or "استراتژی شخصی"
        name_en = payload.get("name_en") or payload.get("key") or "Custom Strategy"
        key = payload.get("key") or "custom_strategy"

        structure_tf = payload.get("structure_tf") or payload.get("timeframes", {}).get("structure", "4h")
        entry_tf = payload.get("entry_tf") or payload.get("timeframes", {}).get("entry", "1h")
        filter_tf = payload.get("filter_tf") or payload.get("timeframes", {}).get("filter", "15m")

        patterns_dict = payload.get("patterns", {})
        candlesticks_dict = payload.get("candlesticks", {})
        indicators_dict = payload.get("indicators", {})
        risk_dict = payload.get("risk", {})

        # Build list of active pattern tokens
        patterns_list = []
        if patterns_dict.get("bos"):
            patterns_list.append("bullish_bos")
        if patterns_dict.get("ob"):
            patterns_list.append("demand_order_block")
        if patterns_dict.get("fvg"):
            patterns_list.append("fvg_mitigation")
        if patterns_dict.get("sr"):
            patterns_list.append("support_resistance")
        if patterns_dict.get("flag"):
            patterns_list.append("flag")
        if patterns_dict.get("flat"):
            patterns_list.append("regular_flat")
        if patterns_dict.get("wedge"):
            patterns_list.append("wedge")

        candlestick_list = []
        if candlesticks_dict.get("engulfing"):
            candlestick_list.append("bullish_engulfing")
        if candlesticks_dict.get("pinbar"):
            candlestick_list.append("bullish_pinbar")
        if candlesticks_dict.get("hammer"):
            candlestick_list.append("hammer")
        if candlesticks_dict.get("morning_star"):
            candlestick_list.append("morning_star")

        rsi_min = indicators_dict.get("rsi_min", 40)
        rsi_max = indicators_dict.get("rsi_max", 70)
        volume_min_ratio = 1.2 if indicators_dict.get("volume_ma_confirmation", True) else 1.0
        min_score = indicators_dict.get("min_score", 6)
        ai_required = payload.get("ai_confirmation_required", False)

        min_rr = risk_dict.get("min_risk_reward", 2.0)
        sl_type = risk_dict.get("stop_loss_type", "swing_low")
        tp1_ratio = risk_dict.get("tp1_ratio", 1.5)
        tp2_ratio = risk_dict.get("tp2_ratio", 3.0)

        yaml_dict = {
            "meta": {
                "schema_version": "1.0",
                "strategy_version": "1.0.0",
                "engine": {"mode": "hybrid_ai_copilot" if ai_required else "rule_based"},
            },
            "strategy": {
                "key": key,
                "names": {"fa": name_fa, "en": name_en},
                "family": payload.get("family", "custom"),
                "description": {
                    "fa": payload.get("description_fa", f"استراتژی سفارشی ساخته شده توسط کاربر: {name_fa}"),
                    "en": payload.get("description_en", f"Custom strategy created by user: {name_en}"),
                },
                "tags": ["custom", "user-created"] + ([f"tf-{entry_tf}"]),
                "is_builtin": False,
            },
            "timeframes": {
                "structure": structure_tf,
                "entry": entry_tf,
                "filter": filter_tf,
            },
            "patterns": patterns_list,
            "candlesticks": candlestick_list,
            "parameters": {
                "min_score": min_score,
                "min_rr": min_rr,
                "rsi_range": {"long": [rsi_min, rsi_max]},
                "volume_min_ratio": volume_min_ratio,
                "require_ai_confirmation": ai_required,
            },
            "exit_rules": {
                "stop_loss": {"method": sl_type, "margin_pct": 0.15},
                "targets": {
                    "tp1": {"risk_reward": tp1_ratio, "auto_breakeven": True},
                    "tp2": {"risk_reward": tp2_ratio, "trailing_stop": True, "partial_close_pct": 50},
                },
            },
        }

        return yaml.dump(yaml_dict, allow_unicode=True, sort_keys=False)

    @classmethod
    def save_custom_strategy(cls, payload: dict[str, Any]) -> str:
        """Serialize payload, write to disk, and register in StrategyRegistry."""
        key = payload.get("key", "custom_strat")
        yaml_content = cls.json_to_yaml_content(payload)
        
        file_path = STRATEGIES_DIR / f"{key}.yaml"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        logger.info("Saved custom strategy YAML to %s", file_path)

        # Register in strategy registry
        registry = get_strategy_registry()
        registry.register_from_yaml(yaml_content, overwrite=True)
        return key


_custom_strat_mgr: CustomStrategyManager | None = None


def get_custom_strategy_manager() -> CustomStrategyManager:
    global _custom_strat_mgr
    if _custom_strat_mgr is None:
        _custom_strat_mgr = CustomStrategyManager()
    return _custom_strat_mgr
