# backend/tests/test_wave_ml.py
"""
Unit tests for the WaveMLScorer module.
Verifies standardized feature extraction, heuristic fallback, self-training, and model persistence.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.ml.wave_scorer import FEATURE_NAMES, WaveMLScorer


def test_feature_extraction_dimension():
    """Verify that feature extraction produces exactly 7 numerical elements."""
    scorer = WaveMLScorer()
    mock_pat = MagicMock()
    mock_pat.retr_a = 0.618
    mock_pat.retr_b = 1.35
    mock_pat.retr_c = 0.85
    mock_pat.slope_ratio = 1.4
    mock_pat.er_b = 0.22
    mock_pat.chop_b = 40.0
    mock_pat.dtw_score = 0.08

    features = scorer.extract_feature_vector(mock_pat)
    assert len(features) == len(FEATURE_NAMES)
    assert features[0] == 0.618
    assert features[1] == 1.35


def test_heuristic_fallback_scoring(tmp_path):
    """Verify deterministic probability bounds without a trained model file."""
    scorer = WaveMLScorer(model_dir=tmp_path)
    mock_pat = MagicMock()
    mock_pat.retr_b = 1.25
    mock_pat.er_b = 0.20

    pat_prob, win_prob, engine = scorer.score_pattern(mock_pat, rr_val=2.5)
    assert 90 <= pat_prob <= 98
    assert 68 <= win_prob <= 95
    assert engine == "HEURISTIC_BENCHMARK"


def test_invalidated_and_target_hit_bounds():
    """Verify that invalidated and target-hit states override scores deterministically."""
    scorer = WaveMLScorer()
    mock_pat = MagicMock()

    # Invalidated -> 0%
    pat_p, win_p, engine = scorer.score_pattern(mock_pat, is_invalidated=True)
    assert pat_p == 0
    assert win_p == 0
    assert engine == "INVALIDATED"

    # Target hit -> 100% win
    pat_p2, win_p2, engine2 = scorer.score_pattern(mock_pat, is_target_hit=True)
    assert pat_p2 == 98
    assert win_p2 == 100
    assert engine2 == "TARGET_HIT"


def test_model_training_and_inference(tmp_path):
    """Verify that train_model fits a scikit-learn model and enables ML inference."""
    scorer = WaveMLScorer(model_dir=tmp_path)

    # Synthetic training samples (10 positive, 10 negative)
    samples = []
    for i in range(10):
        # Successful patterns (higher slope, low ER, good retr_c)
        samples.append({
            "features": [0.60, 1.40, 0.78, 1.80, 0.15, 35.0, 0.04],
            "label": 1,
        })
        # Invalidated patterns (low slope, high ER, bad retr_c)
        samples.append({
            "features": [0.30, 1.05, 1.02, 0.85, 0.55, 65.0, 0.30],
            "label": 0,
        })

    train_res = scorer.train_model(samples, model_filename="test_scorer.joblib")
    assert train_res["status"] == "success"
    assert train_res["samples_count"] == 20
    assert "feature_importances" in train_res

    # Test live prediction with trained model
    test_pat = MagicMock()
    test_pat.retr_a = 0.60
    test_pat.retr_b = 1.40
    test_pat.retr_c = 0.78
    test_pat.slope_ratio = 1.80
    test_pat.er_b = 0.15
    test_pat.chop_b = 35.0
    test_pat.dtw_score = 0.04

    pat_p, win_p, engine = scorer.score_pattern(test_pat)
    assert engine == "TRAINED_ML_MODEL"
    assert 50 <= win_p <= 95
