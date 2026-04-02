"""
GigShield ML Risk Model (v2)
Random Forest trained on synthetic data (default 50k samples)
Provides `risk_model` instance with `train_on_synthetic_data` and `predict_risk`.
"""

try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    import joblib
    SKLEARN_AVAILABLE = True
except Exception:
    np = None
    pd = None
    RandomForestRegressor = None
    StandardScaler = None
    train_test_split = None
    joblib = None
    SKLEARN_AVAILABLE = False

import os
from datetime import datetime


class GigShieldRiskModel:
    """
    Predicts disruption risk for gig workers
    Improved version: trains on larger synthetic dataset by default
    """

    def __init__(self):
        self.model = None
        # Initialize scaler only if sklearn available
        self.scaler = StandardScaler() if StandardScaler is not None else None
        self.is_trained = False

        self.feature_names = [
            'historical_rain_risk',
            'historical_heat_risk',
            'historical_flood_risk',
            'weather_forecast_risk',
            'season_factor',
            'location_density',
            'platform_volatility',
            'worker_experience_days',
            'worker_avg_daily_income',
            'historical_claim_rate',
            'current_aqi',
            'is_festival_season',
        ]

    def train_on_synthetic_data(self, n_samples: int = 50000):
        """
        Train the Random Forest model on synthetic data.
        Default n_samples=50_000 for Member 1 requirement.
        Returns training metrics.
        """
        if not SKLEARN_AVAILABLE:
            print("⚠️ scikit-learn / numpy / pandas not available — skipping ML training.")
            return {"train_score": 0.0, "test_score": 0.0, "feature_importance": {}}

        print(f"🔄 Training Random Forest model on {n_samples} synthetic samples...")

        np.random.seed(42)

        X = self._generate_synthetic_features(n_samples)
        y = self._generate_synthetic_targets(X)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Fit scaler
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Random Forest
        self.model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
        self.model.fit(X_train_scaled, y_train)

        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)

        self.is_trained = True

        self._save_model()

        print(f"✅ Model trained — train R^2: {train_score:.4f}, test R^2: {test_score:.4f}")

        return {"train_score": train_score, "test_score": test_score, "feature_importance": self.get_feature_importance()}

    def _generate_synthetic_features(self, n_samples: int):
        X = np.zeros((n_samples, len(self.feature_names)))

        X[:, 0] = np.random.beta(2, 5, n_samples) * 100  # rain
        X[:, 1] = np.random.beta(3, 4, n_samples) * 100  # heat
        X[:, 2] = np.clip(X[:, 0] * 0.7 + np.random.normal(0, 10, n_samples), 0, 100)  # flood
        X[:, 3] = np.random.beta(3, 4, n_samples) * 100  # forecast risk
        X[:, 4] = np.random.choice([0.2, 0.5, 0.8], n_samples, p=[0.3, 0.4, 0.3])
        X[:, 5] = np.random.beta(2, 2, n_samples)
        X[:, 6] = np.random.beta(2, 3, n_samples)
        exp_days = np.random.exponential(200, n_samples)
        X[:, 7] = np.clip(exp_days / 1000, 0, 1)
        income = np.random.uniform(200, 2000, n_samples)
        X[:, 8] = (income - 200) / 1800
        X[:, 9] = np.random.beta(1, 5, n_samples)
        X[:, 10] = np.random.gamma(2, 50, n_samples) / 500
        X[:, 11] = np.random.choice([0, 1], n_samples, p=[0.7, 0.3])

        return X

    def _generate_synthetic_targets(self, X):
        risk = (
            X[:, 0] * 0.15 +
            X[:, 1] * 0.12 +
            X[:, 2] * 0.10 +
            X[:, 3] * 0.12 +
            X[:, 4] * 0.50 * 100 +
            X[:, 5] * 0.05 * 100 +
            X[:, 6] * 0.08 * 100 +
            (1 - X[:, 7]) * 0.10 * 100 +
            X[:, 8] * 0.03 * 100 +
            X[:, 9] * 0.15 * 100 +
            X[:, 10] * 0.10 * 100 +
            X[:, 11] * 0.10 * 100
        )

        noise = np.random.normal(0, 5, len(risk))
        return np.clip(risk + noise, 0, 100)

    def predict_risk(self, worker_data):
        if not self.is_trained:
            return self._fallback_heuristic(worker_data)

        features = self._extract_features(worker_data)
        features_scaled = self.scaler.transform([features])
        risk_score = float(self.model.predict(features_scaled)[0])

        if risk_score < 30:
            band = "Low"
        elif risk_score < 60:
            band = "Medium"
        else:
            band = "High"

        confidence = self._calculate_confidence(worker_data)

        return {"risk_score": round(risk_score, 1), "risk_band": band, "confidence": confidence, "feature_importance": self.get_top_features(3)}

    def _extract_features(self, worker_data):
        features = []
        city = worker_data.get('city', 'Bangalore')

        city_risks = {
            'Mumbai': {'rain': 85, 'heat': 40, 'flood': 90},
            'Delhi': {'rain': 30, 'heat': 85, 'flood': 20},
            'Chennai': {'rain': 75, 'heat': 70, 'flood': 80},
            'Kolkata': {'rain': 80, 'heat': 65, 'flood': 85},
            'Bangalore': {'rain': 50, 'heat': 35, 'flood': 30},
            'Hyderabad': {'rain': 45, 'heat': 70, 'flood': 35},
            'Pune': {'rain': 55, 'heat': 45, 'flood': 40}
        }

        risks = city_risks.get(city, {'rain': 40, 'heat': 50, 'flood': 30})

        features.append(risks['rain'] / 100)
        features.append(risks['heat'] / 100)
        features.append(risks['flood'] / 100)
        features.append(worker_data.get('weather_forecast_risk', 0.5))

        month = datetime.now().month
        if month in [6, 7, 8, 9]:
            features.append(0.8)
        elif month in [3, 4, 5]:
            features.append(0.6)
        else:
            features.append(0.3)

        density_map = {'Mumbai': 0.9, 'Delhi': 0.85, 'Bangalore': 0.7, 'Pune': 0.6}
        features.append(density_map.get(city, 0.5))

        platform_map = {'Zomato': 0.3, 'Swiggy': 0.3, 'Zepto': 0.5, 'Dunzo': 0.4}
        features.append(platform_map.get(worker_data.get('platform'), 0.3))

        exp_days = worker_data.get('experience_days', 30)
        features.append(min(exp_days / 1000, 1.0))

        income = worker_data.get('avg_daily_income', 500)
        features.append((income - 200) / 1800)

        features.append(worker_data.get('historical_claim_rate', 0.1))
        features.append(worker_data.get('current_aqi', 0.3))
        now = datetime.now()
        is_festival = 1 if (now.month in [10, 11, 12]) or (now.month in [3, 4]) else 0
        features.append(is_festival)

        return features

    def get_feature_importance(self):
        if not self.model:
            return {}
        importance = dict(zip(self.feature_names, self.model.feature_importances_))
        return {k: round(v, 4) for k, v in sorted(importance.items(), key=lambda x: x[1], reverse=True)}

    def get_top_features(self, n=3):
        imp = self.get_feature_importance()
        return dict(list(imp.items())[:n])

    def _save_model(self):
        if joblib is None:
            print("⚠️ joblib not available — skipping model save.")
            return
        os.makedirs('models', exist_ok=True)
        joblib.dump(self.model, 'models/gigshield_risk_model.pkl')
        joblib.dump(self.scaler, 'models/gigshield_scaler.pkl')
        print("✅ Model saved to models/")

    def load_model(self):
        if joblib is None:
            print("⚠️ joblib not available — cannot load saved model.")
            return False
        try:
            self.model = joblib.load('models/gigshield_risk_model.pkl')
            self.scaler = joblib.load('models/gigshield_scaler.pkl')
            self.is_trained = True
            print("✅ Model loaded from disk")
            return True
        except Exception:
            print("⚠️ No saved model found")
            return False

    def _fallback_heuristic(self, worker_data):
        city_risk = {'Mumbai': 70, 'Delhi': 65, 'Bangalore': 40}
        base = city_risk.get(worker_data.get('city'), 50)
        return {"risk_score": base, "risk_band": "Medium" if 30 < base < 70 else ("High" if base >= 70 else "Low"), "confidence": 50, "note": "Using fallback (ML not ready)"}

    def _calculate_confidence(self, worker_data):
        required_fields = ['city', 'platform', 'avg_daily_income']
        present = sum(1 for f in required_fields if f in worker_data)
        return (present / len(required_fields)) * 100


# Single instance
risk_model = GigShieldRiskModel()
