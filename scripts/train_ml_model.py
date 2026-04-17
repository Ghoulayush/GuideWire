"""
Train and save the GigShield Random Forest model offline.

Usage:
    python scripts/train_ml_model.py

This will attempt to load an existing model; if none is found,
it will train on synthetic data and save the model and scaler
into the `models/` directory.
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path so `app` package can be imported
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.ml_risk import risk_model


def main():
    print("Starting offline training script...")
    if risk_model.load_model():
        print("Model already exists on disk. No training needed.")
        return

    print("Training model on synthetic data (this may take a minute)...")
    # train with 50k samples by default for Member 1
    result = risk_model.train_on_synthetic_data(n_samples=50000)
    print("Training complete.")
    print("Train score:", result.get("train_score"))
    print("Test score:", result.get("test_score"))
    print("Model artifacts saved to: models/")


if __name__ == "__main__":
    main()
