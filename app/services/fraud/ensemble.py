"""CPU-friendly Fraud Ensemble using RandomForest.

Combines lightweight detectors (location, collusion, image, isolation)
into a meta-classifier trained on synthetic data. Falls back to a simple
weighted rule when no model is available.
"""
from typing import Dict, Any, Optional
import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier


class FraudEnsemble:
    def __init__(self, model_path: str = "models/fraud_ensemble.pkl") -> None:
        self.model_path = model_path
        self.model: Optional[RandomForestClassifier] = None
        self.is_trained = False
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.is_trained = True
            except Exception:
                self.model = None
                self.is_trained = False

    def _feature_vector(self, features: Dict[str, float]):
        vec = [
            float(features.get("location_score", 0.0)),
            float(features.get("collusion_score", 0.0)),
            float(features.get("image_prob", 0.0)),
            float(features.get("isolation_score", 0.0)),
            float(features.get("claimed_ratio", 0.0)),
            float(features.get("event_count", 0.0)),
        ]
        return np.array(vec).reshape(1, -1)

    def predict_proba(self, features: Dict[str, float]) -> float:
        """Return fraud probability in [0.0, 1.0].

        If no trained model available, use a conservative weighted heuristic.
        """
        if self.model is None:
            # fallback weighted rule (normalize image_prob to 0-100 scale)
            score = (
                features.get("location_score", 0) * 0.25
                + features.get("collusion_score", 0) * 0.35
                + features.get("image_prob", 0) * 100.0 * 0.25
                + features.get("isolation_score", 0) * 0.15
                + features.get("claimed_ratio", 0) * 5.0
            )
            prob = min(1.0, max(0.0, score / 100.0))
            return prob

        X = self._feature_vector(features)
        try:
            p = float(self.model.predict_proba(X)[0, 1])
            return p
        except Exception:
            return 0.0

    def train_on_synthetic(self, n_samples: int = 5000, save: bool = True) -> Dict[str, Any]:
        """Train a RandomForest on synthetic normal/fraud examples.

        Returns a small report dict.
        """
        n_fraud = int(n_samples * 0.12)
        n_normal = n_samples - n_fraud
        X = []
        y = []

        # Normal samples
        for _ in range(n_normal):
            loc = float(np.random.uniform(0, 30))
            coll = float(np.random.uniform(0, 20))
            img = float(np.random.uniform(0, 0.15))
            iso = float(np.random.uniform(0, 20))
            ratio = float(np.random.uniform(0.0, 1.0))
            events = int(np.random.poisson(1) + 1)
            X.append([loc, coll, img, iso, ratio, events])
            y.append(0)

        # Fraud samples
        for _ in range(n_fraud):
            loc = float(np.random.uniform(40, 100))
            coll = float(np.random.uniform(30, 100))
            img = float(np.random.uniform(0.3, 1.0))
            iso = float(np.random.uniform(40, 100))
            ratio = float(np.random.uniform(2.0, 6.0))
            events = int(np.random.poisson(3) + 2)
            X.append([loc, coll, img, iso, ratio, events])
            y.append(1)

        X = np.array(X)
        y = np.array(y)

        clf = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42)
        clf.fit(X, y)
        self.model = clf
        self.is_trained = True

        if save:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(clf, self.model_path)

        return {"n_samples": n_samples, "fraud_fraction": n_fraud / n_samples}

    def load_model(self, path: Optional[str] = None) -> bool:
        p = path or self.model_path
        if os.path.exists(p):
            try:
                self.model = joblib.load(p)
                self.is_trained = True
                return True
            except Exception:
                self.model = None
        return False
