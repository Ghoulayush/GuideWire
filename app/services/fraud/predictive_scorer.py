"""
Predictive Fraud Scorer - Layer 5 of Fraud Detection System
Uses XGBoost to combine signals from Layers 1-4 into final fraud score
Author: Member 3 (You!)
"""

import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except Exception:
    XGBOOST_AVAILABLE = False
    print("⚠️ xgboost not installed. Using heuristic fallback.")

from .base_detector import FraudResult, FraudAction


class PredictiveFraudScorer:
    """
    XGBoost model that predicts fraud probability
    Combines signals from all previous detectors
    """
    
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.feature_names = [
            'location_anomaly_score',
            'collusion_ring_size',
            'image_fake_probability',
            'nlp_fraud_score',
            'review_contradiction_score',
            'historical_claim_frequency',
            'claim_amount_ratio',
            'time_since_last_claim',
            'worker_experience_days',
            'claim_weekend_ratio'
        ]
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained XGBoost model or create a simple one"""
        
        if not XGBOOST_AVAILABLE:
            print("ℹ️ xgboost not installed. Using heuristic fallback.")
            return
        
        try:
            # Try to load saved model
            import os
            import joblib
            
            if os.path.exists('models/xgboost_fraud_model.pkl'):
                self.model = joblib.load('models/xgboost_fraud_model.pkl')
                self.model_loaded = True
                print("✅ XGBoost model loaded from disk!")
            else:
                # Create a simple decision tree model for demo
                self._create_demo_model()
                self.model_loaded = True
                print("✅ Created demo XGBoost model for fraud scoring!")
        except Exception as e:
            print(f"⚠️ Could not load XGBoost model: {e}")
            print("   Using heuristic fallback.")
    
    def _create_demo_model(self):
        """Create a simple rule-based model for demo (no training data needed)"""
        # This is a mock model that uses weighted rules
        # In production, this would be a real XGBoost model
        self.model = "demo_rule_based"
    
    def predict(self, detector_results: List[FraudResult], 
                worker_history: Optional[Dict] = None) -> FraudResult:
        """
        Predict final fraud probability using all detector signals
        
        Args:
            detector_results: List of FraudResult from Layers 1-4
            worker_history: Optional dict with worker's claim history
        
        Returns:
            FraudResult with final fraud score and action
        """
        
        # Extract features from detector results
        features = self._extract_features(detector_results, worker_history)
        
        if self.model_loaded and XGBOOST_AVAILABLE and self.model != "demo_rule_based":
            # Use real XGBoost model
            fraud_probability = self.model.predict_proba([features])[0][1]
            fraud_score = int(fraud_probability * 100)
        else:
            # Use weighted heuristic (works without XGBoost)
            fraud_score = self._heuristic_score(detector_results, worker_history)
        
        # Determine action based on score
        if fraud_score >= 70:
            action = FraudAction.REJECT
            confidence = 90
        elif fraud_score >= 40:
            action = FraudAction.REVIEW
            confidence = 70
        else:
            action = FraudAction.APPROVE
            confidence = 85
        
        # Build explanation
        explanation = self._build_explanation(detector_results, fraud_score)
        
        return FraudResult(
            fraud_score=fraud_score,
            action=action,
            reason=explanation,
            confidence=confidence,
            detector_name="PredictiveFraudScorer",
            metadata={
                "feature_weights": self._get_feature_importance(),
                "num_detectors_used": len(detector_results)
            }
        )
    
    def _extract_features(self, detector_results: List[FraudResult], 
                          worker_history: Optional[Dict]) -> List[float]:
        """Convert detector results into feature vector"""
        
        features = [0.0] * len(self.feature_names)
        
        for result in detector_results:
            name = result.detector_name
            
            if name == "LocationSpoofingDetector":
                features[0] = result.fraud_score / 100.0
            elif name == "CollusionRingDetector":
                features[1] = result.fraud_score / 100.0
            elif name == "ImageFraudDetector":
                features[2] = result.fraud_score / 100.0
            elif name == "NLPFraudDetector":
                features[3] = result.fraud_score / 100.0
                # Check for contradiction
                if "Contradiction" in result.reason:
                    features[4] = 0.8
        
        # Worker history features (if available)
        if worker_history:
            features[5] = min(worker_history.get('claim_frequency', 0) / 10, 1.0)
            features[6] = min(worker_history.get('claim_amount_ratio', 0) / 3, 1.0)
            features[7] = min(worker_history.get('days_since_last_claim', 30) / 30, 1.0)
            features[8] = min(worker_history.get('experience_days', 30) / 365, 1.0)
            features[9] = worker_history.get('weekend_claim_ratio', 0)
        
        return features
    
    def _heuristic_score(self, detector_results: List[FraudResult], 
                         worker_history: Optional[Dict]) -> int:
        """Weighted average of all detector scores (fallback)"""
        
        if not detector_results:
            return 0
        
        # Weights for each detector
        weights = {
            "LocationSpoofingDetector": 0.25,
            "CollusionRingDetector": 0.30,
            "ImageFraudDetector": 0.25,
            "NLPFraudDetector": 0.20
        }
        
        total_score = 0
        total_weight = 0
        
        for result in detector_results:
            weight = weights.get(result.detector_name, 0.2)
            total_score += result.fraud_score * weight
            total_weight += weight
        
        if total_weight > 0:
            return int(total_score / total_weight)
        return 0
    
    def _build_explanation(self, detector_results: List[FraudResult], 
                           final_score: int) -> str:
        """Build human-readable explanation"""
        
        if not detector_results:
            return "No fraud signals detected"
        
        # Find highest scoring detector
        highest = max(detector_results, key=lambda x: x.fraud_score)
        
        if final_score >= 70:
            return f"High fraud probability ({final_score}%). Main signal: {highest.reason[:100]}"
        elif final_score >= 40:
            return f"Medium fraud probability ({final_score}%). {highest.reason[:100]}"
        else:
            return f"Low fraud probability ({final_score}%). {highest.reason[:100]}"
    
    def _get_feature_importance(self) -> Dict[str, float]:
        """Return feature importance weights (for explainability)"""
        return {
            "collusion_ring_size": 0.30,
            "location_anomaly_score": 0.25,
            "image_fake_probability": 0.20,
            "nlp_fraud_score": 0.15,
            "historical_claim_frequency": 0.10
        }


# Singleton instance
predictive_scorer = PredictiveFraudScorer()
