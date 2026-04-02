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
        
        # These are the 12 factors that determine risk
        self.feature_names = [
            'historical_rain_risk',      # How often does it rain here?
            'historical_heat_risk',      # How hot does it get?
            'historical_flood_risk',     # Does this area flood?
            'weather_forecast_risk',     # What's the weather next week?
            'season_factor',             # Monsoon/Summer/Winter?
            'location_density',          # Crowded city or sparse?
            'platform_volatility',       # Zomato/Swiggy/Zepto?
            'worker_experience_days',    # How long have they worked?
            'worker_avg_daily_income',   # How much do they earn?
            'historical_claim_rate',     # Have they claimed before?
            'current_aqi',               # Is pollution severe?
            'is_festival_season'         # Diwali/Dussehra time?
        ]
    
    def train_on_synthetic_data(self):
        """
        Train the ML model on synthetic historical data
        In real world, this would use actual claims data
        For hackathon, we generate realistic fake data
        """
        
        # If the heavy ML dependencies are not available, skip training and
        # return a sensible default so the app can continue to run.
        if not SKLEARN_AVAILABLE:
            print("⚠️ scikit-learn / numpy / pandas not available — skipping ML training.")
            return {
                "train_score": 0.0,
                "test_score": 0.0,
                "feature_importance": {}
            }

        print("🔄 Training Random Forest model...")

        # Generate 10,000 synthetic worker records
        n_samples = 10000
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
            n_estimators=100,        # 100 decision trees
            max_depth=10,            # Each tree looks at 10 levels
            random_state=42,         # Reproducible results
            n_jobs=-1                # Use all CPU cores
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

        # Save model for later use (joblib may be None in trimmed environments)
        self._save_model()

        return {
            "train_score": train_score,
            "test_score": test_score,
            "feature_importance": self.get_feature_importance()
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
            X[:, 0] * 0.15 +   # Rain contributes 15%
            X[:, 1] * 0.12 +   # Heat contributes 12%
            X[:, 2] * 0.10 +   # Flood contributes 10%
            X[:, 3] * 0.12 +   # Forecast contributes 12%
            X[:, 4] * 0.50 * 100 +  # Season: monsoon adds risk
            X[:, 5] * 0.05 * 100 +  # Density adds 5%
            X[:, 6] * 0.08 * 100 +  # Platform volatility
            (1 - X[:, 7]) * 0.10 * 100 +  # Less experience = higher risk
            X[:, 8] * 0.03 * 100 +  # Higher income = slightly higher risk
            X[:, 9] * 0.15 * 100 +  # Past claims predict future
            X[:, 10] * 0.10 * 100 +  # Bad AQI adds risk
            X[:, 11] * 0.10 * 100    # Festival adds risk
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
        
        if not self.is_trained:
            # Fallback if model not trained
            return self._fallback_heuristic(worker_data)
        
        # Convert worker data to feature vector
        features = self._extract_features(worker_data)
        
        # Normalize features
        features_scaled = self.scaler.transform([features])
        
        # Predict
        risk_score = self.model.predict(features_scaled)[0]
        
        # Determine risk band
        if risk_score < 30:
            risk_band = "Low"
        elif risk_score < 60:
            risk_band = "Medium"
        else:
            risk_band = "High"
        
        # Calculate confidence (how sure is the model?)
        confidence = self._calculate_confidence(worker_data)
        
        return {
            "risk_score": round(risk_score, 1),
            "risk_band": risk_band,
            "confidence": confidence,
            "feature_importance": self.get_top_features(3)
        }
    
    def _extract_features(self, worker_data):
        """
        Convert worker data into numbers the model understands
        """
        features = []
        
        city = worker_data.get('city', 'Bangalore')
        
        # City risk profiles (based on real data)
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
        
        # 1. Historical rain risk
        features.append(risks['rain'] / 100)
        
        # 2. Historical heat risk
        features.append(risks['heat'] / 100)
        
        # 3. Historical flood risk
        features.append(risks['flood'] / 100)
        
        # 4. Weather forecast risk (simplified for demo)
        features.append(0.5)  # Will be replaced by real API
        
        # 5. Season factor
        month = datetime.now().month
        if month in [6, 7, 8, 9]:
            features.append(0.8)  # Monsoon
        elif month in [3, 4, 5]:
            features.append(0.6)  # Summer
        else:
            features.append(0.3)  # Winter/Spring
        
        # 6. Location density
        density_map = {'Mumbai': 0.9, 'Delhi': 0.85, 'Bangalore': 0.7, 'Pune': 0.6}
        features.append(density_map.get(city, 0.5))
        
        # 7. Platform volatility
        platform_map = {'Zomato': 0.3, 'Swiggy': 0.3, 'Zepto': 0.5, 'Dunzo': 0.4}
        features.append(platform_map.get(worker_data.get('platform'), 0.3))
        
        # 8. Worker experience (normalized)
        exp_days = worker_data.get('experience_days', 30)
        features.append(min(exp_days / 1000, 1.0))
        
        # 9. Daily income (normalized)
        income = worker_data.get('avg_daily_income', 500)
        features.append((income - 200) / 1800)
        
        # 10. Historical claim rate
        features.append(worker_data.get('historical_claim_rate', 0.1))
        
        # 11. Current AQI (simplified)
        features.append(0.3)  # Will be replaced by real API
        
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
        return {k: round(v, 4) for k, v in sorted(importance.items(), key=lambda x: x[1], reverse=True)}
    
    def get_top_features(self, n=3):
        """Return top N most important features"""
        importance = self.get_feature_importance()
        return dict(list(importance.items())[:n])
    
    def _save_model(self):
        """Save trained model to disk"""
        if joblib is None:
            print("⚠️ joblib not available — skipping model save.")
            return

        os.makedirs('models', exist_ok=True)
        joblib.dump(self.model, 'models/gigshield_risk_model.pkl')
        joblib.dump(self.scaler, 'models/gigshield_scaler.pkl')
        print("✅ Model saved to models/")
    
    def load_model(self):
        """Load pre-trained model"""
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
        """Simple fallback if ML fails"""
        city_risk = {'Mumbai': 70, 'Delhi': 65, 'Bangalore': 40}
        base = city_risk.get(worker_data.get('city'), 50)
        return {
            "risk_score": base,
            "risk_band": "Medium" if 30 < base < 70 else ("High" if base >= 70 else "Low"),
            "confidence": 50,
            "note": "Using fallback (ML not ready)"
        }
    
    def _calculate_confidence(self, worker_data):
        """How confident is the prediction?"""
        required_fields = ['city', 'platform', 'avg_daily_income']
        present = sum(1 for f in required_fields if f in worker_data)
        return (present / len(required_fields)) * 100


# Create a single instance for the whole app
risk_model = GigShieldRiskModel()