# scripts/train_wave_ml.py
"""
Local Standalone Training Script for Elliott Wave ML Scorer.

Executes local self-supervised training on recorded patterns:
- Reads labeled patterns from data/datasets/recorded_patterns.json
- Bootstraps with calibrated synthetic benchmark samples if dataset < 10
- Trains Scikit-Learn RandomForestClassifier
- Evaluates feature importance and saves artifact to app/ml/models/
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

from app.ml.wave_scorer import FEATURE_NAMES, DEFAULT_MODEL_DIR
from app.ml.pattern_recorder import PATTERNS_DB_PATH

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_wave_ml")


def generate_bootstrap_samples(count: int = 40) -> list[dict[str, Any]]:
    """Generate high-fidelity calibrated samples for initial model bootstrapping."""
    samples = []
    rng = np.random.default_rng(42)

    # 1. Successful patterns (Class 1: Golden ratios, low noise, high RR)
    for _ in range(count // 2):
        retr_a = float(round(rng.uniform(0.58, 0.68), 4))
        retr_b = float(round(rng.uniform(1.20, 1.30), 4))
        retr_c = float(round(rng.uniform(0.78, 0.88), 4))
        slope = float(round(rng.uniform(1.25, 1.60), 2))
        er_b = float(round(rng.uniform(0.15, 0.28), 4))
        chop_b = float(round(rng.uniform(35.0, 50.0), 2))
        dtw = float(round(rng.uniform(0.02, 0.08), 4))
        samples.append({
            "features": [retr_a, retr_b, retr_c, slope, er_b, chop_b, dtw],
            "label": 1,
            "type": "TARGET_HIT",
        })

    # 2. Invalidated patterns (Class 0: High noise, fast slope, deformed ratios)
    for _ in range(count // 2):
        retr_a = float(round(rng.uniform(0.40, 0.52), 4))
        retr_b = float(round(rng.uniform(1.02, 1.12), 4))
        retr_c = float(round(rng.uniform(0.50, 0.65), 4))
        slope = float(round(rng.uniform(0.60, 0.95), 2))
        er_b = float(round(rng.uniform(0.45, 0.70), 4))
        chop_b = float(round(rng.uniform(55.0, 75.0), 2))
        dtw = float(round(rng.uniform(0.18, 0.35), 4))
        samples.append({
            "features": [retr_a, retr_b, retr_c, slope, er_b, chop_b, dtw],
            "label": 0,
            "type": "INVALIDATED",
        })

    return samples


def run_training() -> None:
    logger.info("==================================================")
    logger.info("   🚀 AlgoTrade Wave ML Local Model Training")
    logger.info("==================================================")

    labeled_samples: list[dict[str, Any]] = []

    # Read from recorded database if present
    if PATTERNS_DB_PATH.exists():
        try:
            with open(PATTERNS_DB_PATH, "r", encoding="utf-8") as f:
                db_data = json.load(f)
                for item in db_data.values():
                    lbl = item.get("label")
                    feat = item.get("features")
                    if lbl in (0, 1) and feat and len(feat) == len(FEATURE_NAMES):
                        labeled_samples.append({
                            "features": feat,
                            "label": lbl,
                            "type": "TARGET_HIT" if lbl == 1 else "INVALIDATED",
                        })
            logger.info("Loaded %d labeled patterns from %s", len(labeled_samples), PATTERNS_DB_PATH)
        except Exception as e:
            logger.warning("Error reading pattern database: %s", e)

    # If dataset has fewer than 10 samples, augment with bootstrap baseline
    if len(labeled_samples) < 10:
        logger.info("Dataset has <%d samples; augmenting with 40 calibrated bootstrap baseline samples...", 10)
        bootstraps = generate_bootstrap_samples(40)
        labeled_samples.extend(bootstraps)

    X = np.array([s["features"] for s in labeled_samples])
    y = np.array([s["label"] for s in labeled_samples])

    logger.info("Training Matrix: X shape = %s, Target balance: %d wins / %d losses",
                X.shape, int(np.sum(y == 1)), int(np.sum(y == 0)))

    clf = RandomForestClassifier(n_estimators=60, max_depth=4, random_state=42)
    clf.fit(X, y)

    y_pred = clf.predict(X)
    acc = accuracy_score(y, y_pred)
    logger.info("Model In-Sample Accuracy: %.2f%%", acc * 100)

    out_file = DEFAULT_MODEL_DIR / "running_flat_scorer.joblib"
    DEFAULT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, out_file)
    logger.info("✅ Trained model saved successfully to: %s", out_file)

    logger.info("\n--- Feature Importances Breakdown ---")
    for name, imp in sorted(zip(FEATURE_NAMES, clf.feature_importances_), key=lambda x: x[1], reverse=True):
        bar = "█" * int(imp * 40)
        logger.info("  %-12s: %5.2f%% | %s", name, imp * 100, bar)

    logger.info("\n--- Classification Report ---")
    report = classification_report(y, y_pred, target_names=["INVALIDATED", "TARGET_HIT"])
    print(report)
    logger.info("Training pipeline finished successfully! Model is active for live scoring.")


if __name__ == "__main__":
    run_training()
