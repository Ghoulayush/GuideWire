"""
Temporal Fraud Detector - Layer 6 of Fraud Detection System
Detects unusual claim patterns over time using LSTM + heuristics
Author: Member 3 (You!)
"""

import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque

try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    TENSORFLOW_AVAILABLE = True
except Exception:
    TENSORFLOW_AVAILABLE = False
    print("⚠️ tensorflow not installed. Using heuristic fallback.")

from .base_detector import FraudResult, FraudAction


class TemporalFraudDetector:
    """
    Detects anomalous claim patterns over time
    Uses LSTM to learn normal patterns, flags deviations
    """
    
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.claim_history = {}  # Store claim history per worker
        self._load_model()
    
    def _load_model(self):
        """Load or create LSTM model for temporal detection"""
        
        if not TENSORFLOW_AVAILABLE:
            print("ℹ️ tensorflow not installed. Using heuristic fallback.")
            return
        
        try:
            # Create a simple LSTM model for sequence prediction
            self.model = Sequential([
                LSTM(32, activation='relu', input_shape=(30, 5), return_sequences=True),
                Dropout(0.2),
                LSTM(16, activation='relu'),
                Dropout(0.2),
                Dense(8, activation='relu'),
                Dense(1, activation='sigmoid')
            ])
            self.model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
            self.model_loaded = True
            print("✅ LSTM temporal model created for fraud detection!")
        except Exception as e:
            print(f"⚠️ Could not create LSTM model: {e}")
            print("   Using heuristic fallback.")
    
    def detect(self, worker_id: str, claim_history: List[Dict]) -> FraudResult:
        """
        Detect temporal anomalies in claim patterns
        
        Args:
            worker_id: Unique worker identifier
            claim_history: List of past claims with timestamps and amounts
        
        Returns:
            FraudResult with fraud_score, action, reason, confidence
        """
        
        fraud_score = 0
        reasons = []
        
        if not claim_history:
            return FraudResult(
                fraud_score=0,
                action=FraudAction.APPROVE,
                reason="No claim history available",
                confidence=90,
                detector_name="TemporalFraudDetector"
            )
        
        # Check 1: Sudden claim spike (3x normal)
        weekly_claims = self._get_weekly_counts(claim_history)
        if len(weekly_claims) >= 4:  # At least 4 weeks of data
            last_week = weekly_claims[-1]
            avg_previous = sum(weekly_claims[:-1]) / len(weekly_claims[:-1])
            
            if avg_previous > 0 and last_week > avg_previous * 3:
                fraud_score += 45
                reasons.append(f"Sudden claim spike: {last_week} claims vs avg {avg_previous:.1f}")
        
        # Check 2: Weekend-only claims pattern
        weekend_ratio = self._calculate_weekend_ratio(claim_history)
        if weekend_ratio > 0.8:  # 80%+ claims on weekends
            fraud_score += 35
            reasons.append(f"Weekend claim pattern: {weekend_ratio:.0%} on Sat/Sun")
        
        # Check 3: Claim timing consistency (same time each day)
        hour_consistency = self._calculate_hour_consistency(claim_history)
        if hour_consistency < 0.2:  # Very inconsistent times
            fraud_score += 15
            reasons.append("Random claim times (possible bot pattern)")
        
        # Check 4: Same amount repeating (pattern fraud)
        amount_variance = self._calculate_amount_variance(claim_history)
        if amount_variance < 0.1:  # Very little variance in claim amounts
            fraud_score += 25
            reasons.append("Identical claim amounts repeated (pattern fraud)")
        
        # Check 5: Claim frequency decay (new worker suddenly claiming)
        if len(claim_history) >= 10:
            first_5_avg = sum(c['amount'] for c in claim_history[:5]) / 5
            last_5_avg = sum(c['amount'] for c in claim_history[-5:]) / 5
            if last_5_avg > first_5_avg * 2:
                fraud_score += 30
                reasons.append(f"Claim amount escalation: +{((last_5_avg/first_5_avg)-1)*100:.0%}")
        
        # Check 6: Rapid succession claims (within hours)
        rapid_claims = self._detect_rapid_succession(claim_history)
        if rapid_claims > 3:
            fraud_score += 40
            reasons.append(f"{rapid_claims} claims within 24 hours (rapid succession)")
        
        # Use LSTM if available for more accurate detection
        if self.model_loaded and len(claim_history) >= 30:
            lstm_score = self._lstm_predict(claim_history)
            fraud_score = max(fraud_score, lstm_score)
            reasons.append(f"LSTM anomaly score: {lstm_score}")
        
        # Cap fraud score
        fraud_score = min(fraud_score, 100)
        
        # Determine action
        if fraud_score >= 65:
            action = FraudAction.REJECT
        elif fraud_score >= 35:
            action = FraudAction.REVIEW
        else:
            action = FraudAction.APPROVE
        
        reason = " | ".join(reasons) if reasons else "Normal claim pattern detected"
        
        return FraudResult(
            fraud_score=fraud_score,
            action=action,
            reason=reason,
            confidence=75 if fraud_score > 0 else 85,
            detector_name="TemporalFraudDetector",
            metadata={
                "total_claims": len(claim_history),
                "weekend_ratio": weekend_ratio,
                "rapid_claims": rapid_claims if 'rapid_claims' in dir() else 0
            }
        )
    
    def _get_weekly_counts(self, claims: List[Dict]) -> List[int]:
        """Calculate number of claims per week"""
        if not claims:
            return []
        
        weekly = []
        current_week = None
        count = 0
        
        for claim in claims:
            date = claim.get('date', datetime.now())
            week = date.isocalendar()[1]
            
            if current_week is None:
                current_week = week
            
            if week == current_week:
                count += 1
            else:
                weekly.append(count)
                current_week = week
                count = 1
        
        if count > 0:
            weekly.append(count)
        
        return weekly
    
    def _calculate_weekend_ratio(self, claims: List[Dict]) -> float:
        """Calculate percentage of claims on weekends"""
        if not claims:
            return 0
        
        weekend_count = 0
        for claim in claims:
            date = claim.get('date', datetime.now())
            # Saturday = 5, Sunday = 6 (depending on datetime weekday)
            if date.weekday() >= 5:
                weekend_count += 1
        
        return weekend_count / len(claims)
    
    def _calculate_hour_consistency(self, claims: List[Dict]) -> float:
        """Calculate how consistent claim times are"""
        if len(claims) < 5:
            return 1.0
        
        hours = [c.get('date', datetime.now()).hour for c in claims]
        unique_hours = len(set(hours))
        
        return unique_hours / 24  # Lower = more consistent (suspicious)
    
    def _calculate_amount_variance(self, claims: List[Dict]) -> float:
        """Calculate variance in claim amounts"""
        if len(claims) < 2:
            return 1.0
        
        amounts = [c.get('amount', 0) for c in claims]
        mean = sum(amounts) / len(amounts)
        
        if mean == 0:
            return 1.0
        
        variance = sum((a - mean) ** 2 for a in amounts) / len(amounts)
        return variance / mean  # Normalized variance
    
    def _detect_rapid_succession(self, claims: List[Dict]) -> int:
        """Detect multiple claims within 24 hours"""
        if len(claims) < 2:
            return 0
        
        rapid_count = 0
        for i in range(1, len(claims)):
            prev_date = claims[i-1].get('date', datetime.now())
            curr_date = claims[i].get('date', datetime.now())
            
            if (curr_date - prev_date) < timedelta(hours=24):
                rapid_count += 1
        
        return rapid_count
    
    def _lstm_predict(self, claims: List[Dict]) -> int:
        """Use LSTM to predict anomaly score"""
        # Prepare sequence data
        sequence = self._prepare_sequence(claims)
        
        if sequence is None or len(sequence) < 30:
            return 0
        
        try:
            # Reshape for LSTM
            X = np.array(sequence).reshape(1, 30, 5)
            prediction = float(self.model.predict(X, verbose=0)[0][0])
            return int(prediction * 100)
        except Exception:
            return 0
    
    def _prepare_sequence(self, claims: List[Dict]) -> Optional[List]:
        """Prepare sequence data for LSTM"""
        if len(claims) < 30:
            return None
        
        # Take last 30 claims
        recent = claims[-30:]
        sequence = []
        
        for claim in recent:
            # Create feature vector for each claim
            features = [
                claim.get('amount', 0) / 1000,  # Normalized amount
                claim.get('hour', 12) / 24,     # Hour of day
                1 if claim.get('is_weekend', False) else 0,
                claim.get('days_since_last', 30) / 30,
                claim.get('severity', 3) / 5
            ]
            sequence.append(features)
        
        return sequence


# Singleton instance
temporal_detector = TemporalFraudDetector()
