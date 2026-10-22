# tests/test_condition_evaluator.py
"""Tests for the CEL-like condition evaluator."""

from app.strategy.condition_evaluator import (
    evaluate_conditions,
    evaluate_single_condition,
)


class TestSingleCondition:
    """Test individual condition expression evaluation."""

    def test_boolean_path_true(self):
        features = {"structure": {"valid": True}}
        assert evaluate_single_condition("features.structure.valid", features)

    def test_boolean_path_false(self):
        features = {"structure": {"valid": False}}
        assert not evaluate_single_condition("features.structure.valid", features)

    def test_negation(self):
        features = {"invalidated": False}
        assert evaluate_single_condition("!features.invalidated", features)

    def test_negation_true_path(self):
        features = {"invalidated": True}
        assert not evaluate_single_condition("!features.invalidated", features)

    def test_gte_comparison(self):
        features = {"rr": {"value": 1.8}}
        assert evaluate_single_condition("features.rr.value >= 1.5", features)

    def test_gte_comparison_exact(self):
        features = {"rr": {"value": 1.5}}
        assert evaluate_single_condition("features.rr.value >= 1.5", features)

    def test_gte_comparison_fail(self):
        features = {"rr": {"value": 1.2}}
        assert not evaluate_single_condition("features.rr.value >= 1.5", features)

    def test_lt_comparison(self):
        features = {"impulses": {"i2_slope_ratio": 0.5}}
        assert evaluate_single_condition(
            "features.impulses.i2_slope_ratio < 0.7", features
        )

    def test_string_equality(self):
        context = {"direction": "LONG"}
        assert evaluate_single_condition(
            "context.direction == 'LONG'", {}, context
        )

    def test_string_inequality(self):
        context = {"direction": "SHORT"}
        assert not evaluate_single_condition(
            "context.direction == 'LONG'", {}, context
        )

    def test_missing_path_returns_false(self):
        features = {}
        assert not evaluate_single_condition(
            "features.nonexistent.path >= 1.0", features
        )

    def test_empty_expression(self):
        assert evaluate_single_condition("", {})

    def test_deeply_nested_path(self):
        features = {"rr": {"by_entry": {"entry_b": 1.7}}}
        assert evaluate_single_condition(
            "features.rr.by_entry.entry_b >= 1.5", features
        )


class TestConditionBlocks:
    """Test all/any/none condition block evaluation."""

    def test_all_pass(self):
        features = {
            "structure": {"valid": True},
            "rr": {"value": 2.0},
        }
        conditions = {
            "all": [
                "features.structure.valid",
                "features.rr.value >= 1.5",
            ]
        }
        assert evaluate_conditions(conditions, features)

    def test_all_one_fails(self):
        features = {
            "structure": {"valid": True},
            "rr": {"value": 1.0},
        }
        conditions = {
            "all": [
                "features.structure.valid",
                "features.rr.value >= 1.5",
            ]
        }
        assert not evaluate_conditions(conditions, features)

    def test_any_one_passes(self):
        features = {
            "pattern": {"bullish": True, "bearish": False},
        }
        conditions = {
            "any": [
                "features.pattern.bullish",
                "features.pattern.bearish",
            ]
        }
        assert evaluate_conditions(conditions, features)

    def test_any_none_pass(self):
        features = {
            "pattern": {"bullish": False, "bearish": False},
        }
        conditions = {
            "any": [
                "features.pattern.bullish",
                "features.pattern.bearish",
            ]
        }
        assert not evaluate_conditions(conditions, features)

    def test_none_block(self):
        features = {"invalidated": False}
        conditions = {"none": ["features.invalidated"]}
        assert evaluate_conditions(conditions, features)

    def test_none_block_fails(self):
        features = {"invalidated": True}
        conditions = {"none": ["features.invalidated"]}
        assert not evaluate_conditions(conditions, features)

    def test_combined_all_and_none(self):
        features = {
            "structure_valid": True,
            "invalidated": False,
            "rr": {"by_entry": {"entry_b": 1.8}},
        }
        conditions = {
            "all": [
                "features.structure_valid",
                "features.rr.by_entry.entry_b >= 1.5",
            ],
            "none": ["features.invalidated"],
        }
        assert evaluate_conditions(conditions, features)

    def test_empty_conditions_pass(self):
        assert evaluate_conditions({}, {})
        assert evaluate_conditions({"all": []}, {})
