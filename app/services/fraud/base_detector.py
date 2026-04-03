"""
Base Detector - Unified Output Format for All Fraud Detectors
All detectors must return this exact format
"""
from typing import Dict, Any, Optional
from enum import Enum
try:
    from pydantic import BaseModel
except Exception:
    # Lightweight fallback if pydantic not available
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def dict(self, **kwargs):
            return {k: getattr(self, k) for k in self.__dict__}


class FraudAction(str, Enum):
    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    REJECT = "REJECT"


class FraudResult(BaseModel):
    """Standard output format for ALL fraud detectors"""
    fraud_score: int  # 0-100, higher = more suspicious
    action: FraudAction
    reason: str
    confidence: int  # 0-100, how sure the model is
    detector_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    # Provide a model_dump compatibility wrapper to support pydantic v2 and v1
    def model_dump(self, exclude_none: bool = True) -> Dict[str, Any]:
        if hasattr(super(), "model_dump"):
            try:
                return super().model_dump(exclude_none=exclude_none)
            except Exception:
                pass
        # fallback to dict-like
        if hasattr(self, "dict"):
            return self.dict(exclude_none=exclude_none) if callable(getattr(self, "dict")) else self.__dict__
        return {k: getattr(self, k) for k in self.__dict__}


def standardize_result(raw_result: Dict[str, Any], detector_name: str) -> FraudResult:
    """
    Convert any detector output to standard FraudResult format
    Handles different possible input formats
    """
    # Extract fraud_score
    fraud_score = raw_result.get("fraud_score", raw_result.get("score", 0))
    if isinstance(fraud_score, float):
        fraud_score = int(fraud_score)
    try:
        fraud_score = int(fraud_score)
    except Exception:
        fraud_score = 0

    # Extract action
    action_str = raw_result.get("action", "REVIEW")
    try:
        action = FraudAction(action_str.upper())
    except Exception:
        action = FraudAction.REVIEW

    # Extract reason
    reason = raw_result.get("reason", f"Analysis from {detector_name}")

    # Extract confidence
    confidence = raw_result.get("confidence", 50)
    if isinstance(confidence, float):
        confidence = int(confidence)
    try:
        confidence = int(confidence)
    except Exception:
        confidence = 50

    metadata = raw_result.get("metadata") or raw_result.get("details")

    return FraudResult(
        fraud_score=fraud_score,
        action=action,
        reason=reason,
        confidence=confidence,
        detector_name=detector_name,
        metadata=metadata,
    )
