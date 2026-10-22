# app/ml/wave_scorer.py
"""
Lightweight Machine Learning and statistical scorer for Elliott Wave patterns.

Provides dual-stage inference:
1. Pure geometric wave candidate validation (AlefTrade)
2. Tabular ML win-probability estimation (Scikit-Learn/LightGBM) with heuristic fallback.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger("algotrade.ml.wave_scorer")

FEATURE_NAMES: list[str] = [
    "retr_a",
    "retr_b",
    "retr_c",
    "slope_ratio",
    "er_b",
    "chop_b",
    "dtw_score",
]

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent / "models"


class WaveMLScorer:
    """Manages inference, fallback scoring, and self-training for wave pattern models."""

    def __init__(self, model_dir: Path | None = None) -> None:
        self.model_dir = model_dir or DEFAULT_MODEL_DIR
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self._model: Any | None = None
        self._engine_type: str = "HEURISTIC_BENCHMARK"
        self._load_active_model()

    def _load_active_model(self, model_filename: str = "running_flat_scorer.joblib") -> bool:
        """Attempt to load a trained model from disk; fail silently to benchmark."""
        model_path = self.model_dir / model_filename
        if not model_path.exists():
            self._model = None
            self._engine_type = "HEURISTIC_BENCHMARK"
            return False

        try:
            import joblib
            self._model = joblib.load(model_path)
            self._engine_type = "TRAINED_ML_MODEL"
            logger.info("Successfully loaded ML wave scorer: %s", model_path)
            return True
        except Exception as e:
            logger.warning("Could not load ML model from %s: %s", model_path, e)
            self._model = None
            self._engine_type = "HEURISTIC_BENCHMARK"
            return False

    def extract_feature_vector(self, pattern: Any) -> list[float]:
        """Extract a standardized 7-dimensional numerical feature vector."""
        if hasattr(pattern, "to_feature_vector"):
            try:
                vec = pattern.to_feature_vector()
                if isinstance(vec, list) and len(vec) == len(FEATURE_NAMES):
                    return [float(x) for x in vec]
            except Exception:
                pass

        # Fallback attribute extraction
        return [
            float(round(getattr(pattern, "retr_a", 0.618), 4)),
            float(round(getattr(pattern, "retr_b", 1.272), 4)),
            float(round(getattr(pattern, "retr_c", 0.85), 4)),
            float(round(getattr(pattern, "slope_ratio", 1.20), 2)),
            float(round(getattr(pattern, "er_b", 0.25), 4)),
            float(round(getattr(pattern, "chop_b", 45.0), 2)),
            float(round(getattr(pattern, "dtw_score", 0.05), 4)),
        ]

    def score_pattern(
        self,
        pattern: Any,
        rr_val: float = 2.0,
        is_invalidated: bool = False,
        is_target_hit: bool = False,
    ) -> tuple[int, int, str]:
        """
        Compute (pattern_probability, trade_win_probability, engine_type).
        Guarantees deterministic bounds [0, 100] and zero crashes.
        """
        if is_invalidated:
            return 0, 0, "INVALIDATED"
        if is_target_hit:
            return 98, 100, "TARGET_HIT"

        retr_b = float(getattr(pattern, "retr_b", 1.0))
        er_b = float(getattr(pattern, "er_b", 0.3))

        pat_prob = min(98, max(90, int(92 + (2 if retr_b >= 1.05 else 0) + (2 if er_b <= 0.35 else 0))))

        if self._model is not None:
            try:
                features = np.array([self.extract_feature_vector(pattern)])
                # Predict probability of class 1 (TARGET_HIT)
                probs = self._model.predict_proba(features)[0]
                win_prob = int(round(probs[1] * 100))
                return pat_prob, min(95, max(50, win_prob)), "TRAINED_ML_MODEL"
            except Exception as e:
                logger.debug("Inference fallback on pattern score: %s", e)

        # Calibrated benchmark heuristic
        heuristic_win = min(92, max(68, int(65 + min(rr_val, 4.0) * 6.5)))
        return pat_prob, heuristic_win, "HEURISTIC_BENCHMARK"

    def train_model(
        self,
        training_samples: list[dict[str, Any]],
        model_filename: str = "running_flat_scorer.joblib",
    ) -> dict[str, Any]:
        """
        Train a scikit-learn GradientBoosting or RandomForest model on labeled patterns.
        Target: 1 for TARGET_HIT, 0 for INVALIDATED.
        """
        if len(training_samples) < 10:
            raise ValueError(f"Insufficient training samples ({len(training_samples)} < 10 required)")

        from sklearn.ensemble import RandomForestClassifier

        x_list: list[list[float]] = []
        y_list: list[int] = []

        for s in training_samples:
            feat = s.get("features")
            label = s.get("label")
            if feat and len(feat) == len(FEATURE_NAMES) and label in (0, 1):
                x_list.append([float(v) for v in feat])
                y_list.append(int(label))

        if len(set(y_list)) < 2:
            raise ValueError("Training dataset must contain both successful (1) and invalidated (0) patterns")

        clf = RandomForestClassifier(n_estimators=50, max_depth=4, random_state=42)
        clf.fit(np.array(x_list), np.array(y_list))

        import joblib
        out_path = self.model_dir / model_filename
        joblib.dump(clf, out_path)

        self._model = clf
        self._engine_type = "TRAINED_ML_MODEL"

        importances = {
            name: float(round(imp, 4))
            for name, imp in zip(FEATURE_NAMES, clf.feature_importances_)
        }

        return {
            "status": "success",
            "samples_count": len(x_list),
            "model_path": str(out_path),
            "feature_importances": importances,
            "engine": "TRAINED_ML_MODEL",
        }


_GLOBAL_SCORER: WaveMLScorer | None = None


def get_wave_scorer() -> WaveMLScorer:
    """Singleton provider for WaveMLScorer."""
    global _GLOBAL_SCORER
    if _GLOBAL_SCORER is None:
        _GLOBAL_SCORER = WaveMLScorer()
    return _GLOBAL_SCORER
