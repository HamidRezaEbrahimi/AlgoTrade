# tests/test_yaml_strategy.py
"""Tests for YAML strategy loading, validation, and evaluation."""

from pathlib import Path

import pytest

from app.strategy.base_strategy import StrategyEvalContext
from app.strategy.feature_calculator import compute_wave_features
from app.strategy.yaml_strategy import YAMLStrategy

STRATEGIES_DIR = Path(__file__).parent.parent / "app" / "strategy" / "strategies"


class TestYAMLStrategyLoading:
    """Test loading strategies from YAML files."""

    def test_load_price_action_8criteria(self):
        path = STRATEGIES_DIR / "price_action_8criteria.yaml"
        strategy = YAMLStrategy(yaml_path=str(path))
        meta = strategy.get_metadata()
        assert meta.key == "price_action_8criteria"
        assert meta.is_builtin is True
        assert meta.family == "price_action"
        assert "پرایس‌اکشن" in meta.name_fa

    def test_load_regular_flat(self):
        path = STRATEGIES_DIR / "regular_flat.yaml"
        strategy = YAMLStrategy(yaml_path=str(path))
        meta = strategy.get_metadata()
        assert meta.key == "regular_flat"
        assert meta.family == "corrective"

    def test_load_flag(self):
        path = STRATEGIES_DIR / "flag.yaml"
        strategy = YAMLStrategy(yaml_path=str(path))
        meta = strategy.get_metadata()
        assert meta.key == "flag"
        assert meta.family == "continuation"

    def test_load_wedge(self):
        path = STRATEGIES_DIR / "wedge.yaml"
        strategy = YAMLStrategy(yaml_path=str(path))
        meta = strategy.get_metadata()
        assert meta.key == "wedge"
        assert meta.family == "reversal"


class TestYAMLStrategyValidation:
    """Test strategy configuration validation."""

    def test_valid_strategy_no_errors(self):
        path = STRATEGIES_DIR / "price_action_8criteria.yaml"
        strategy = YAMLStrategy(yaml_path=str(path))
        errors = strategy.validate_config()
        assert errors == []

    def test_invalid_yaml_missing_key(self):
        yaml_content = """
meta:
  schema_version: "1.0"
strategy:
  names:
    fa: "تست"
    en: "Test"
entry_conditions:
  all: []
outcome_scenarios:
  - id: "FALLBACK"
    priority: 999
    conditions:
      all: []
    outcome:
      reason_fa: "پیش‌فرض"
"""
        strategy = YAMLStrategy(yaml_content=yaml_content)
        errors = strategy.validate_config()
        assert "strategy.key is required" in errors

    def test_invalid_yaml_no_scenarios(self):
        yaml_content = """
meta:
  schema_version: "1.0"
strategy:
  key: "test"
  names:
    fa: "تست"
    en: "Test"
entry_conditions:
  all: []
outcome_scenarios: []
"""
        strategy = YAMLStrategy(yaml_content=yaml_content)
        errors = strategy.validate_config()
        assert any("outcome_scenario" in e for e in errors)


class TestWavePatternEvaluation:
    """Test wave-pattern strategy evaluation."""

    def test_regular_flat_ideal_signal(self):
        """Complete regular flat with strong slope and high RR → signal."""
        path = STRATEGIES_DIR / "regular_flat.yaml"
        strategy = YAMLStrategy(yaml_path=str(path))

        # Simulate a completed Regular Flat
        ctx = StrategyEvalContext(
            symbol="BTCUSDT",
            current_price=67000.0,  # P5 - above P4
            timestamp=None,
            wave_points={
                "P0": 60000.0,   # Impulse1 start
                "P1": 65000.0,   # Impulse1 end
                "P2": 61500.0,   # A end (retrace)
                "P3": 64800.0,   # B end
                "P4": 60200.0,   # C end (below A)
                "P5": 67000.0,   # Impulse2 end
            },
        )

        signal = strategy.evaluate(ctx)
        assert signal is not None
        assert signal.symbol == "BTCUSDT"
        assert signal.reason_code == "YAML_regular_flat"

    def test_regular_flat_pending_no_signal(self):
        """Incomplete pattern (i2 not crossed P4) → no signal (low confidence)."""
        path = STRATEGIES_DIR / "regular_flat.yaml"
        strategy = YAMLStrategy(yaml_path=str(path))

        # i2 has NOT crossed P4 yet
        ctx = StrategyEvalContext(
            symbol="BTCUSDT",
            current_price=59800.0,  # Below P4
            timestamp=None,
            wave_points={
                "P0": 60000.0,
                "P1": 65000.0,
                "P2": 61500.0,
                "P3": 64800.0,
                "P4": 60200.0,
                "P5": 59800.0,  # Still below P4
            },
        )

        signal = strategy.evaluate(ctx)
        # Entry conditions require i2_crossed_P4 → should be None
        assert signal is None

    def test_flag_strategy_evaluation(self):
        """Flag pattern with strong breakout → signal."""
        path = STRATEGIES_DIR / "flag.yaml"
        strategy = YAMLStrategy(yaml_path=str(path))

        ctx = StrategyEvalContext(
            symbol="ETHUSDT",
            current_price=3900.0,
            timestamp=None,
            wave_points={
                "P0": 3380.0,
                "P1": 3500.0,   # Strong impulse
                "P2": 3450.0,   # Shallow retracement (flag)
                "P3": 3480.0,
                "P4": 3420.0,
                "P5": 3900.0,   # Breakout above P4 with strong extension
            },
        )

        signal = strategy.evaluate(ctx)
        assert signal is not None
        assert signal.reason_code == "YAML_flag"


class TestFeatureCalculator:
    """Test wave feature computation."""

    def test_compute_wave_features_basic(self):
        points = {
            "P0": 100.0,
            "P1": 150.0,  # i1 = 50
            "P2": 130.0,  # A = 20 (retr = 20/50 = 0.4)
            "P3": 145.0,  # B = 15
            "P4": 110.0,  # C = 35
            "P5": 160.0,  # i2 = 50
        }
        features = compute_wave_features(points, 160.0)

        assert features["structure_valid"] is True
        assert features["completion"]["i2_crossed_P4"] is True
        assert features["direction"]["i2_opposes_C"] is True
        assert features["metrics"]["wave_a_retr"] == pytest.approx(0.4, abs=0.01)
        assert features["impulses"]["i2_slope_ratio"] == pytest.approx(1.0, abs=0.01)

    def test_compute_wave_features_incomplete(self):
        """P5 still below P4 → not completed."""
        points = {
            "P0": 100.0,
            "P1": 150.0,
            "P2": 130.0,
            "P3": 145.0,
            "P4": 110.0,
            "P5": 105.0,  # Below P4
        }
        features = compute_wave_features(points, 105.0)
        assert features["completion"]["i2_crossed_P4"] is False
