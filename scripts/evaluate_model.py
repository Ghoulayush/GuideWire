"""
Evaluate the saved Random Forest model on synthetic data and save a local report.

Usage:
    python scripts/evaluate_model.py

This runs only locally and writes `models/eval_report.json`.
DO NOT push `models/` to GitHub.
"""

import sys
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.ml_risk import risk_model

try:
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
except Exception:
    print("scikit-learn not available; install requirements to evaluate.")
    sys.exit(2)


def main():
    print("Loading model (from models/)...")
    loaded = risk_model.load_model()
    if not loaded:
        print("No saved model found; training now (synthetic data)...")
        risk_model.train_on_synthetic_data()

    model = risk_model.model
    scaler = risk_model.scaler
    if model is None or scaler is None:
        print("Model or scaler missing. Cannot evaluate.")
        return 2

    n_samples = 5000
    print(f"Generating {n_samples} synthetic samples for evaluation...")
    X = risk_model._generate_synthetic_features(n_samples)
    y = risk_model._generate_synthetic_targets(X)

    X_scaled = scaler.transform(X)

    print("Predicting...")
    y_pred = model.predict(X_scaled)

    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)
    rmse = math.sqrt(mse)
    mae = mean_absolute_error(y, y_pred)

    print("\nEvaluation metrics:")
    print(f"  R^2: {r2:.4f}")
    print(f"  MSE : {mse:.4f}")
    print(f"  RMSE: {rmse:.4f}")
    print(f"  MAE : {mae:.4f}")

    fi = risk_model.get_feature_importance()
    print("\nTop feature importances:")
    for i, (k, v) in enumerate(list(fi.items())[:10], 1):
        print(f"  {i}. {k}: {v:.4f}")

    # Sample comparisons
    idxs = random.sample(range(n_samples), 10)
    samples = []
    print("\nSample true -> pred:")
    for idx in idxs:
        t = float(y[idx])
        p = float(y_pred[idx])
        samples.append({"true": t, "pred": p})
        print(f"  {t:.2f} -> {p:.2f}")

    report = {
        "r2": float(r2),
        "mse": float(mse),
        "rmse": float(rmse),
        "mae": float(mae),
        "feature_importance": fi,
        "samples": samples,
    }

    out_path = Path("models") / "eval_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    print(f"\nSaved local evaluation report to: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())