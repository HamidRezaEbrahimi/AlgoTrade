# tests/test_strategy_registry.py
"""Tests for the strategy registry."""

import pytest

from app.strategy.strategy_registry import StrategyRegistry


class TestStrategyRegistry:
    """Test strategy registration and discovery."""

    def test_load_builtins(self):
        registry = StrategyRegistry()
        count = registry.load_builtins()
        assert count >= 3  # price_action_8criteria, regular_flat, flag, wedge

    def test_list_all(self):
        registry = StrategyRegistry()
        registry.load_builtins()
        all_strategies = registry.list_all()
        keys = [m.key for m in all_strategies]
        assert "price_action_8criteria" in keys
        assert "regular_flat" in keys
        assert "flag" in keys
        assert "wedge" in keys

    def test_get_strategy_by_key(self):
        registry = StrategyRegistry()
        registry.load_builtins()
        strategy = registry.get("regular_flat")
        assert strategy is not None
        meta = strategy.get_metadata()
        assert meta.name_fa == "رگولار فلت"

    def test_get_nonexistent_returns_none(self):
        registry = StrategyRegistry()
        registry.load_builtins()
        assert registry.get("nonexistent_key") is None

    def test_register_custom_strategy(self):
        registry = StrategyRegistry()
        yaml_content = """
meta:
  schema_version: "1.0"
  engine:
    mode: "wave_pattern"
strategy:
  key: "custom_test"
  names:
    fa: "استراتژی تست"
    en: "Test Strategy"
  family: "custom"
  tags: ["test"]
entry_conditions:
  all:
    - "features.structure_valid"
outcome_scenarios:
  - id: "MATCH"
    priority: 10
    conditions:
      all: []
    outcome:
      confidence: 50
      reason_fa: "تست"
"""
        meta = registry.register_from_yaml(yaml_content)
        assert meta.key == "custom_test"
        assert registry.count == 1

    def test_cannot_overwrite_builtin(self):
        registry = StrategyRegistry()
        registry.load_builtins()
        yaml_content = """
meta:
  schema_version: "1.0"
  engine:
    mode: "price_action"
strategy:
  key: "price_action_8criteria"
  names:
    fa: "جایگزین"
    en: "Replacement"
  is_builtin: true
entry_conditions:
  all: []
outcome_scenarios:
  - id: "FALLBACK"
    priority: 999
    conditions:
      all: []
    outcome:
      reason_fa: "test"
"""
        with pytest.raises(ValueError, match="built-in"):
            registry.register_from_yaml(yaml_content)

    def test_remove_custom_strategy(self):
        registry = StrategyRegistry()
        yaml_content = """
meta:
  schema_version: "1.0"
  engine:
    mode: "wave_pattern"
strategy:
  key: "to_delete"
  names:
    fa: "حذف شونده"
    en: "To Delete"
  family: "custom"
entry_conditions:
  all: []
outcome_scenarios:
  - id: "F"
    priority: 999
    conditions:
      all: []
    outcome:
      reason_fa: "x"
"""
        registry.register_from_yaml(yaml_content)
        assert registry.count == 1
        removed = registry.remove("to_delete")
        assert removed is True
        assert registry.count == 0

    def test_cannot_remove_builtin(self):
        registry = StrategyRegistry()
        registry.load_builtins()
        with pytest.raises(ValueError, match="built-in"):
            registry.remove("price_action_8criteria")

    def test_list_builtin_vs_custom(self):
        registry = StrategyRegistry()
        registry.load_builtins()
        builtins = registry.list_builtin()
        customs = registry.list_custom()
        assert len(builtins) >= 3
        assert len(customs) == 0
        assert all(m.is_builtin for m in builtins)
