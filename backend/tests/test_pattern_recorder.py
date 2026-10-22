# tests/test_pattern_recorder.py
"""
Tests for PatternRecorder, Quality Grading (PQS), and Recording Modes.
"""
import shutil
import tempfile
from pathlib import Path

import pytest
from app.ml.pattern_recorder import PatternRecorder, compute_pattern_quality


@pytest.fixture
def temp_recorder():
    temp_dir = Path(tempfile.mkdtemp())
    rec = PatternRecorder()
    rec.config_path = temp_dir / "test_config.json"
    rec.db_path = temp_dir / "test_db.json"
    rec._mode = "auto"
    yield rec
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_quality_grading_strong():
    """Verify golden ratios yield STRONG grade (Score >= 80)."""
    res = compute_pattern_quality(
        retr_a=0.618,
        retr_b=1.272,
        retr_c=0.85,
        slope_ratio=1.45,
        er_b=0.20,
        dtw_score=0.04,
        rr_ratio=2.8,
    )
    assert res.score >= 80
    assert res.grade == "STRONG"
    assert res.grade_color == "#10b981"
    assert len(res.strengths) >= 2


def test_quality_grading_normal_and_weak():
    """Verify moderate and noisy patterns yield NORMAL and WEAK grades."""
    # Normal
    res_normal = compute_pattern_quality(
        retr_a=0.52,
        retr_b=1.15,
        retr_c=0.70,
        slope_ratio=1.1,
        er_b=0.35,
        dtw_score=0.12,
        rr_ratio=1.8,
    )
    assert 55 <= res_normal.score < 80
    assert res_normal.grade == "NORMAL"

    # Weak (noisy, fast retracement, low RR)
    res_weak = compute_pattern_quality(
        retr_a=0.40,
        retr_b=1.02,
        retr_c=0.50,
        slope_ratio=0.7,
        er_b=0.60,
        dtw_score=0.30,
        rr_ratio=1.1,
    )
    assert res_weak.score < 55
    assert res_weak.grade == "WEAK"
    assert res_weak.grade_color == "#f59e0b"
    assert len(res_weak.cautions) >= 1


def test_recording_modes_behavior(temp_recorder):
    """Test auto, manual, and disabled recording modes."""
    sample_pattern = {
        "id": "pat_test_101",
        "name": "Running Flat",
        "direction": "bullish",
        "retr_a": 0.618,
        "retr_b": 1.272,
        "retr_c": 0.85,
        "slope_ratio": 1.3,
        "er_b": 0.22,
        "dtw_score": 0.05,
        "lifecycle_status": "ACTIVE",
    }

    # 1. Mode: Auto -> records automatically
    temp_recorder.save_config("auto")
    item1 = temp_recorder.record_pattern(sample_pattern, symbol="BTCUSDT", timeframe="1h", is_manual=False)
    assert item1 is not None
    assert item1["id"] == "pat_test_101"
    assert item1["recorded_mode"] == "auto"

    # 2. Mode: Manual -> ignores automatic calls, records manual calls
    temp_recorder.save_config("manual")
    item2 = temp_recorder.record_pattern(sample_pattern, symbol="BTCUSDT", timeframe="1h", is_manual=False)
    assert item2 is None  # Auto call ignored in manual mode

    item2_manual = temp_recorder.record_pattern(sample_pattern, symbol="BTCUSDT", timeframe="1h", is_manual=True)
    assert item2_manual is not None
    assert item2_manual["recorded_mode"] == "manual"

    # 3. Mode: Disabled -> blocks all recording
    temp_recorder.save_config("disabled")
    item3 = temp_recorder.record_pattern(sample_pattern, symbol="BTCUSDT", timeframe="1h", is_manual=True)
    assert item3 is None


def test_lifecycle_update_and_deduplication(temp_recorder):
    """Test that pattern status updates (ACTIVE -> TARGET_HIT) without duplication."""
    temp_recorder.save_config("auto")
    pat = {
        "id": "running_flat_007",
        "name": "Running Flat",
        "lifecycle_status": "ACTIVE",
        "retr_a": 0.618,
        "retr_b": 1.272,
        "retr_c": 0.85,
    }

    # Record initially as ACTIVE
    res1 = temp_recorder.record_pattern(pat, symbol="EURUSD", timeframe="15m")
    assert res1["lifecycle_status"] == "ACTIVE"
    assert res1["label"] is None

    # Update to TARGET_HIT
    pat["lifecycle_status"] = "TARGET_HIT"
    res2 = temp_recorder.record_pattern(pat, symbol="EURUSD", timeframe="15m")
    assert res2["lifecycle_status"] == "TARGET_HIT"
    assert res2["label"] == 1

    records = temp_recorder.get_recordings()
    assert len(records) == 1  # Deduplication maintained
    assert records[0]["lifecycle_status"] == "TARGET_HIT"
