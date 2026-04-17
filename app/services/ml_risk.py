"""
GigShield ML Risk Model
AI-powered risk prediction using Random Forest
Author: Member 1
"""

# Optional heavy dependencies: numpy, pandas, scikit-learn, joblib
try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    import joblib

    SKLEARN_AVAILABLE = True
except Exception:
    # If these packages aren't available in the runtime, fall back to a
    # lightweight mode that avoids importing/using them. The app will still
    # run using the fallback heuristic provided by `predict_risk` when the
    # model is not trained.
    np = None
    pd = None
    RandomForestRegressor = None
    StandardScaler = None
    train_test_split = None
    joblib = None
    SKLEARN_AVAILABLE = False

import os
from datetime import datetime


MODEL_VERSION = "risk-v3"
FEATURE_SCHEMA_VERSION = "risk-features-v1"


class GigShieldRiskModel:
    """
    Predicts disruption risk for gig delivery workers
    Uses 12 features to output risk score (0-100)
    """

    def __init__(self):
        self.model = None
        # Initialize scaler only if sklearn's StandardScaler was imported
        self.scaler = StandardScaler() if StandardScaler is not None else None
        self.is_trained = False
        self.model_version = MODEL_VERSION
        self.feature_schema_version = FEATURE_SCHEMA_VERSION
        self.training_mode = "untrained"
        self.trained_at = None
        self.last_training_metrics = {}
        self.scenario_catalog_version = "scenarios-v1"
        self.total_predictions = 0
        self.fallback_predictions = 0
        self.low_confidence_escalations = 0

        # These are the 12 factors that determine risk
        self.feature_names = [
            "historical_rain_risk",  # How often does it rain here?
            "historical_heat_risk",  # How hot does it get?
            "historical_flood_risk",  # Does this area flood?
            "weather_forecast_risk",  # What's the weather next week?
            "season_factor",  # Monsoon/Summer/Winter?
            "location_density",  # Crowded city or sparse?
            "platform_volatility",  # Zomato/Swiggy/Zepto?
            "worker_experience_days",  # How long have they worked?
            "worker_avg_daily_income",  # How much do they earn?
            "historical_claim_rate",  # Have they claimed before?
            "current_aqi",  # Is pollution severe?
            "is_festival_season",  # Diwali/Dussehra time?
        ]

    def train_on_synthetic_data(self, n_samples: int = 10000):
        """
        Train the ML model on synthetic historical data
        In real world, this would use actual claims data
        For hackathon, we generate realistic fake data
        """

        # If the heavy ML dependencies are not available, skip training and
        # return a sensible default so the app can continue to run.
        if not SKLEARN_AVAILABLE:
            print(
                "⚠️ scikit-learn / numpy / pandas not available — skipping ML training."
            )
            return {
                "train_score": 0.0,
                "test_score": 0.0,
                "feature_importance": {},
                "model_metadata": self.get_model_metadata(),
            }

        print("🔄 Training Random Forest model...")

        # Generate synthetic worker records
        np.random.seed(42)  # So results are reproducible

        # Create synthetic features
        X = self._generate_synthetic_features(n_samples)

        # Create synthetic risk scores (what we want to predict)
        y = self._generate_synthetic_targets(X)

        # Split into training (80%) and testing (20%)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Normalize features (scale to 0-1 range)
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Create Random Forest model
        self.model = RandomForestRegressor(
            n_estimators=100,  # 100 decision trees
            max_depth=10,  # Each tree looks at 10 levels
            random_state=42,  # Reproducible results
            n_jobs=-1,  # Use all CPU cores
        )

        # Train the model
        self.model.fit(X_train_scaled, y_train)

        # Evaluate accuracy
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)

        print(f"✅ Model trained!")
        print(f"   Training accuracy: {train_score:.2%}")
        print(f"   Test accuracy: {test_score:.2%}")

        self.is_trained = True
        self.training_mode = "synthetic"
        self.trained_at = datetime.utcnow().isoformat()
        self.last_training_metrics = {
            "train_score": float(train_score),
            "test_score": float(test_score),
            "n_samples": int(n_samples),
        }

        # Save model for later use (joblib may be None in trimmed environments)
        self._save_model()

        return {
            "train_score": train_score,
            "test_score": test_score,
            "feature_importance": self.get_feature_importance(),
            "model_metadata": self.get_model_metadata(),
        }

    def _generate_synthetic_features(self, n_samples):
        """
        Generate fake but realistic worker data
        """
        X = np.zeros((n_samples, len(self.feature_names)))

        # 1. Historical rain risk (0-100) - Mumbai high, Delhi low
        X[:, 0] = np.random.beta(2, 5, n_samples) * 100

        # 2. Historical heat risk - Delhi high, Mumbai low
        X[:, 1] = np.random.beta(3, 4, n_samples) * 100

        # 3. Historical flood risk - related to rain risk
        X[:, 2] = X[:, 0] * 0.7 + np.random.normal(0, 10, n_samples)
        X[:, 2] = np.clip(X[:, 2], 0, 100)

        # 4. Weather forecast risk (0-100)
        X[:, 3] = np.random.beta(3, 4, n_samples) * 100

        # 5. Season factor (0.2=winter, 0.5=summer, 0.8=monsoon)
        X[:, 4] = np.random.choice([0.2, 0.5, 0.8], n_samples, p=[0.3, 0.4, 0.3])

        # 6. Location density (0-1, 0=rural, 1=urban)
        X[:, 5] = np.random.beta(2, 2, n_samples)

        # 7. Platform volatility (0-1)
        X[:, 6] = np.random.beta(2, 3, n_samples)

        # 8. Worker experience (0-1000 days, normalized)
        exp_days = np.random.exponential(200, n_samples)
        X[:, 7] = np.clip(exp_days / 1000, 0, 1)

        # 9. Daily income (₹200-2000, normalized)
        income = np.random.uniform(200, 2000, n_samples)
        X[:, 8] = (income - 200) / 1800

        # 10. Historical claim rate (0-1)
        X[:, 9] = np.random.beta(1, 5, n_samples)

        # 11. Current AQI (0-500, normalized)
        X[:, 10] = np.random.gamma(2, 50, n_samples) / 500

        # 12. Festival season (0 or 1)
        X[:, 11] = np.random.choice([0, 1], n_samples, p=[0.7, 0.3])

        return X

    def _generate_synthetic_targets(self, X):
        """
        Generate risk scores based on realistic patterns
        """
        risk = (
            X[:, 0] * 0.15  # Rain contributes 15%
            + X[:, 1] * 0.12  # Heat contributes 12%
            + X[:, 2] * 0.10  # Flood contributes 10%
            + X[:, 3] * 0.12  # Forecast contributes 12%
            + X[:, 4] * 0.50 * 100  # Season: monsoon adds risk
            + X[:, 5] * 0.05 * 100  # Density adds 5%
            + X[:, 6] * 0.08 * 100  # Platform volatility
            + (1 - X[:, 7]) * 0.10 * 100  # Less experience = higher risk
            + X[:, 8] * 0.03 * 100  # Higher income = slightly higher risk
            + X[:, 9] * 0.15 * 100  # Past claims predict future
            + X[:, 10] * 0.10 * 100  # Bad AQI adds risk
            + X[:, 11] * 0.10 * 100  # Festival adds risk
        )

        # Add random noise (±5%)
        noise = np.random.normal(0, 5, len(risk))
        risk = risk + noise

        # Keep between 0 and 100
        return np.clip(risk, 0, 100)

    def predict_risk(self, worker_data):
        """
        Predict risk for a specific worker

        Input example:
        worker_data = {
            'city': 'Mumbai',
            'platform': 'Zomato',
            'experience_days': 60,
            'avg_daily_income': 500,
            'historical_claim_rate': 0.1
        }

        Returns:
        {
            'risk_score': 72.5,
            'risk_band': 'High',
            'confidence': 85
        }
        """

        self.total_predictions += 1
        sanitized_data, quality_meta = self._sanitize_worker_data(worker_data)
        confidence = self._calculate_confidence(worker_data, quality_meta)

        if not self.is_trained:
            self.fallback_predictions += 1
            # Fallback if model not trained
            base = self._fallback_heuristic(sanitized_data)
            guarded = self._apply_guardrails(
                worker_data=sanitized_data,
                base_score=float(base.get("risk_score", 50)),
                confidence=confidence,
            )
            final_score = self._clip(float(guarded["final_score"]), 0.0, 100.0)
            return {
                "risk_score": round(final_score, 1),
                "risk_band": self._risk_band(final_score),
                "confidence": confidence,
                "confidence_band": self._confidence_band(confidence),
                "feature_importance": self.get_top_features(3),
                "reason_codes": guarded["reason_codes"],
                "guardrail_adjustment": round(float(guarded["adjustment"]), 1),
                "recommended_action": self._recommended_action(
                    risk_score=final_score, confidence=confidence
                ),
                "note": "Using fallback (ML not ready)",
                "model_metadata": self.get_model_metadata(),
            }

        # Convert worker data to feature vector
        features = self._extract_features(sanitized_data)
        features = self._validate_feature_vector(features)

        # Normalize features
        features_scaled = self.scaler.transform([features])

        # Predict (bounded 0-100)
        raw_score = float(self.model.predict(features_scaled)[0])
        raw_score = self._clip(raw_score, 0.0, 100.0)

        # Hybrid guardrail layer (model score + deterministic policy)
        guarded = self._apply_guardrails(
            worker_data=sanitized_data,
            base_score=raw_score,
            confidence=confidence,
        )
        risk_score = self._clip(float(guarded["final_score"]), 0.0, 100.0)
        risk_band = self._risk_band(risk_score)

        return {
            "risk_score": round(risk_score, 1),
            "risk_band": risk_band,
            "confidence": confidence,
            "confidence_band": self._confidence_band(confidence),
            "feature_importance": self.get_top_features(3),
            "reason_codes": guarded["reason_codes"],
            "guardrail_adjustment": round(float(guarded["adjustment"]), 1),
            "recommended_action": self._recommended_action(
                risk_score=risk_score, confidence=confidence
            ),
            "model_metadata": self.get_model_metadata(),
        }

    def _safe_float(self, value, default: float) -> float:
        try:
            return float(value)
        except Exception:
            return float(default)

    def _clip(self, value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def _sanitize_worker_data(self, worker_data):
        if not isinstance(worker_data, dict):
            worker_data = {}

        quality_meta = {
            "missing_required_fields": [],
            "coerced_fields": [],
            "clipped_fields": [],
        }

        city_raw = worker_data.get("city", "Bangalore")
        city = str(city_raw).strip() if city_raw is not None else "Bangalore"
        platform_raw = worker_data.get("platform", "Zomato")
        platform = str(platform_raw).strip() if platform_raw is not None else "Zomato"

        required_fields = ["city", "platform", "avg_daily_income"]
        for field in required_fields:
            if field not in worker_data or worker_data.get(field) in [None, ""]:
                quality_meta["missing_required_fields"].append(field)

        def parse_numeric(
            field_name: str, default: float, low: float, high: float
        ) -> float:
            raw = worker_data.get(field_name, default)
            parsed = self._safe_float(raw, default)
            if raw != parsed and not isinstance(raw, (int, float)):
                quality_meta["coerced_fields"].append(field_name)
            clipped = self._clip(parsed, low, high)
            if clipped != parsed:
                quality_meta["clipped_fields"].append(field_name)
            return clipped

        experience_days = parse_numeric("experience_days", 30, 0, 5000)
        avg_daily_income = parse_numeric("avg_daily_income", 500, 100, 5000)
        historical_claim_rate = parse_numeric("historical_claim_rate", 0.1, 0, 1)
        weather_forecast_risk = parse_numeric("weather_forecast_risk", 50, 0, 100)
        current_aqi = parse_numeric("current_aqi", 150, 0, 500)

        sanitized = {
            "city": city or "Bangalore",
            "platform": platform or "Zomato",
            "experience_days": experience_days,
            "avg_daily_income": avg_daily_income,
            "historical_claim_rate": historical_claim_rate,
            "weather_forecast_risk": weather_forecast_risk,
            "current_aqi": current_aqi,
        }
        return sanitized, quality_meta

    def _validate_feature_vector(self, features):
        if not isinstance(features, list):
            features = list(features)

        if len(features) != len(self.feature_names):
            if len(features) < len(self.feature_names):
                features = features + [0.0] * (len(self.feature_names) - len(features))
            else:
                features = features[: len(self.feature_names)]

        validated = []
        for value in features:
            numeric = self._safe_float(value, 0.0)
            if np is not None and not np.isfinite(numeric):
                numeric = 0.0
            validated.append(float(numeric))
        return validated

    def _extract_features(self, worker_data):
        """
        Convert worker data into numbers the model understands
        """
        features = []

        city = worker_data.get("city", "Bangalore")

        # City risk profiles (based on real data)
        city_risks = {
            "Mumbai": {"rain": 85, "heat": 40, "flood": 90},
            "Delhi": {"rain": 30, "heat": 85, "flood": 20},
            "Chennai": {"rain": 75, "heat": 70, "flood": 80},
            "Kolkata": {"rain": 80, "heat": 65, "flood": 85},
            "Bangalore": {"rain": 50, "heat": 35, "flood": 30},
            "Hyderabad": {"rain": 45, "heat": 70, "flood": 35},
            "Pune": {"rain": 55, "heat": 45, "flood": 40},
        }

        risks = city_risks.get(city, {"rain": 40, "heat": 50, "flood": 30})

        # 1. Historical rain risk (0-100)
        features.append(risks["rain"])

        # 2. Historical heat risk (0-100)
        features.append(risks["heat"])

        # 3. Historical flood risk (0-100)
        features.append(risks["flood"])

        # 4. Weather forecast risk (0-100)
        features.append(
            self._clip(worker_data.get("weather_forecast_risk", 50), 0, 100)
        )

        # 5. Season factor
        month = datetime.now().month
        if month in [6, 7, 8, 9]:
            features.append(0.8)  # Monsoon
        elif month in [3, 4, 5]:
            features.append(0.6)  # Summer
        else:
            features.append(0.3)  # Winter/Spring

        # 6. Location density
        density_map = {"Mumbai": 0.9, "Delhi": 0.85, "Bangalore": 0.7, "Pune": 0.6}
        features.append(density_map.get(city, 0.5))

        # 7. Platform volatility
        platform_map = {"Zomato": 0.3, "Swiggy": 0.3, "Zepto": 0.5, "Dunzo": 0.4}
        features.append(platform_map.get(worker_data.get("platform"), 0.3))

        # 8. Worker experience (normalized)
        exp_days = worker_data.get("experience_days", 30)
        features.append(min(exp_days / 1000, 1.0))

        # 9. Daily income (normalized)
        income = worker_data.get("avg_daily_income", 500)
        features.append((income - 200) / 1800)

        # 10. Historical claim rate (0-1)
        features.append(self._clip(worker_data.get("historical_claim_rate", 0.1), 0, 1))

        # 11. Current AQI normalized to roughly training scale
        aqi_raw = self._clip(worker_data.get("current_aqi", 150), 0, 500)
        features.append(aqi_raw / 500)

        # 12. Festival season
        now = datetime.now()
        is_festival = 1 if (now.month in [10, 11, 12]) or (now.month in [3, 4]) else 0
        features.append(is_festival)

        return features

    def get_feature_importance(self):
        """
        Returns which factors matter most
        Used for explainability in the dashboard
        """
        if not self.model:
            return {}

        importance = dict(zip(self.feature_names, self.model.feature_importances_))
        # Sort by importance
        return {
            k: round(v, 4)
            for k, v in sorted(importance.items(), key=lambda x: x[1], reverse=True)
        }

    def get_top_features(self, n=3):
        """Return top N most important features"""
        importance = self.get_feature_importance()
        return dict(list(importance.items())[:n])

    def _save_model(self):
        """Save trained model to disk"""
        if joblib is None:
            print("⚠️ joblib not available — skipping model save.")
            return

        os.makedirs("models", exist_ok=True)
        bundle = {
            "model": self.model,
            "scaler": self.scaler,
            "metadata": self.get_model_metadata(),
        }
        joblib.dump(bundle, "models/gigshield_model_bundle.pkl")
        joblib.dump(self.model, "models/gigshield_risk_model.pkl")
        joblib.dump(self.scaler, "models/gigshield_scaler.pkl")
        print("✅ Model saved to models/")

    def load_model(self):
        """Load pre-trained model"""
        if joblib is None:
            print("⚠️ joblib not available — cannot load saved model.")
            return False

        try:
            bundle_path = "models/gigshield_model_bundle.pkl"
            if os.path.exists(bundle_path):
                bundle = joblib.load(bundle_path)
                self.model = bundle.get("model")
                self.scaler = bundle.get("scaler")
                metadata = bundle.get("metadata") or {}
                self.model_version = metadata.get("model_version", self.model_version)
                self.feature_schema_version = metadata.get(
                    "feature_schema_version", self.feature_schema_version
                )
                self.training_mode = metadata.get("training_mode", "synthetic")
                self.trained_at = metadata.get("trained_at")
            else:
                self.model = joblib.load("models/gigshield_risk_model.pkl")
                self.scaler = joblib.load("models/gigshield_scaler.pkl")
                self.training_mode = "legacy"
            self.is_trained = True
            print("✅ Model loaded from disk")
            return True
        except Exception:
            print("⚠️ No saved model found")
            return False

    def _fallback_heuristic(self, worker_data):
        """Simple fallback if ML fails"""
        city_risk = {"Mumbai": 70, "Delhi": 65, "Bangalore": 40}
        base = city_risk.get(worker_data.get("city"), 50)
        return {
            "risk_score": base,
            "risk_band": self._risk_band(base),
            "confidence": 50,
            "note": "Using fallback (ML not ready)",
            "model_metadata": self.get_model_metadata(),
        }

    def _calculate_confidence(self, raw_worker_data, quality_meta):
        """Compute confidence using payload quality and data completeness."""
        if not isinstance(raw_worker_data, dict):
            return 35.0

        required_fields = ["city", "platform", "avg_daily_income"]
        present = sum(
            1
            for f in required_fields
            if f in raw_worker_data and raw_worker_data.get(f) not in [None, ""]
        )

        completeness_score = (present / len(required_fields)) * 100
        missing_penalty = 12 * len(quality_meta.get("missing_required_fields", []))
        coercion_penalty = 4 * len(quality_meta.get("coerced_fields", []))
        clipping_penalty = 3 * len(quality_meta.get("clipped_fields", []))

        confidence = (
            completeness_score - missing_penalty - coercion_penalty - clipping_penalty
        )
        return round(self._clip(confidence, 20, 98), 1)

    def _risk_band(self, risk_score: float) -> str:
        if risk_score < 30:
            return "Low"
        if risk_score < 60:
            return "Medium"
        return "High"

    def _confidence_band(self, confidence: float) -> str:
        if confidence >= 80:
            return "high"
        if confidence >= 55:
            return "medium"
        return "low"

    def _recommended_action(self, risk_score: float, confidence: float) -> str:
        # Conservative escalation when uncertainty is high
        if confidence < 55 and risk_score >= 35:
            self.low_confidence_escalations += 1
            return "REVIEW"
        if risk_score >= 75:
            return "REVIEW_PRIORITY"
        if risk_score >= 60:
            return "REVIEW"
        return "AUTO_APPROVE"

    def _apply_guardrails(self, worker_data, base_score: float, confidence: float):
        adjustment = 0.0
        reason_codes = []

        if worker_data.get("historical_claim_rate", 0) >= 0.35:
            adjustment += 10
            reason_codes.append("CLAIM_RATE_HIGH")

        if worker_data.get("experience_days", 30) < 14:
            adjustment += 8
            reason_codes.append("LOW_EXPERIENCE")

        if worker_data.get("avg_daily_income", 500) < 250:
            adjustment += 4
            reason_codes.append("INCOME_VOLATILITY_RISK")

        if worker_data.get("weather_forecast_risk", 50) >= 75:
            adjustment += 8
            reason_codes.append("WEATHER_EXTREME_FORECAST")

        if worker_data.get("current_aqi", 150) >= 280:
            adjustment += 8
            reason_codes.append("AQI_SEVERE")

        # Conservative uncertainty policy
        if confidence < 55:
            adjustment += 6
            reason_codes.append("LOW_CONFIDENCE_ESCALATION")

        final_score = self._clip(base_score + adjustment, 0, 100)
        if not reason_codes:
            reason_codes.append("BASELINE_RISK_POLICY")

        return {
            "final_score": final_score,
            "adjustment": adjustment,
            "reason_codes": reason_codes,
        }

    def generate_stress_test_scenarios(self):
        """Scenario generator for local robustness checks without historical data."""
        return [
            {
                "scenario": "extreme_rain_flood",
                "payload": {
                    "city": "Mumbai",
                    "platform": "Zomato",
                    "experience_days": 20,
                    "avg_daily_income": 550,
                    "historical_claim_rate": 0.2,
                    "weather_forecast_risk": 90,
                    "current_aqi": 120,
                },
            },
            {
                "scenario": "heatwave_hazardous_aqi",
                "payload": {
                    "city": "Delhi",
                    "platform": "Swiggy",
                    "experience_days": 120,
                    "avg_daily_income": 700,
                    "historical_claim_rate": 0.12,
                    "weather_forecast_risk": 78,
                    "current_aqi": 340,
                },
            },
            {
                "scenario": "new_worker_sparse_data",
                "payload": {
                    "city": "Pune",
                    "platform": "Zepto",
                    "avg_daily_income": 320,
                },
            },
            {
                "scenario": "adversarial_extreme_values",
                "payload": {
                    "city": "Bangalore",
                    "platform": "Dunzo",
                    "experience_days": -100,
                    "avg_daily_income": 999999,
                    "historical_claim_rate": 4.2,
                    "weather_forecast_risk": 1000,
                    "current_aqi": -45,
                },
            },
            {
                "scenario": "high_claim_frequency",
                "payload": {
                    "city": "Kolkata",
                    "platform": "Zomato",
                    "experience_days": 45,
                    "avg_daily_income": 500,
                    "historical_claim_rate": 0.55,
                    "weather_forecast_risk": 72,
                    "current_aqi": 190,
                },
            },
        ]

    def run_stress_test(self):
        """Run scenario predictions and return pass/fail stability summary."""
        scenarios = self.generate_stress_test_scenarios()
        results = []
        failures = []

        for item in scenarios:
            scenario = item["scenario"]
            out = self.predict_risk(item["payload"])
            score = float(out.get("risk_score", 0))

            valid = 0 <= score <= 100
            has_band = out.get("risk_band") in {"Low", "Medium", "High"}
            has_reasons = bool(out.get("reason_codes"))

            if not (valid and has_band and has_reasons):
                failures.append(
                    {
                        "scenario": scenario,
                        "valid_score": valid,
                        "valid_band": has_band,
                        "has_reasons": has_reasons,
                    }
                )

            results.append(
                {
                    "scenario": scenario,
                    "risk_score": out.get("risk_score"),
                    "risk_band": out.get("risk_band"),
                    "confidence": out.get("confidence"),
                    "confidence_band": out.get("confidence_band"),
                    "recommended_action": out.get("recommended_action"),
                    "reason_codes": out.get("reason_codes"),
                }
            )

        return {
            "scenario_catalog_version": self.scenario_catalog_version,
            "total_scenarios": len(scenarios),
            "passed": len(failures) == 0,
            "failures": failures,
            "results": results,
            "model_metadata": self.get_model_metadata(),
        }

    def get_model_metadata(self):
        return {
            "model_version": self.model_version,
            "feature_schema_version": self.feature_schema_version,
            "trained_at": self.trained_at,
            "training_mode": self.training_mode,
            "scenario_catalog_version": self.scenario_catalog_version,
        }

    def get_runtime_diagnostics(self):
        fallback_rate = 0.0
        if self.total_predictions > 0:
            fallback_rate = (self.fallback_predictions / self.total_predictions) * 100

        return {
            "total_predictions": self.total_predictions,
            "fallback_predictions": self.fallback_predictions,
            "fallback_rate": round(fallback_rate, 2),
            "low_confidence_escalations": self.low_confidence_escalations,
            "is_trained": self.is_trained,
        }


# Create a single instance for the whole app
risk_model = GigShieldRiskModel()
