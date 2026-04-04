from datetime import date, datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class PersonaType(str, Enum):
    BIKE = "bike"
    SCOOTER = "scooter"
    CAR = "car"


class OnboardRequest(BaseModel):
    worker_id: str = Field(..., description="Unique ID from platform (e.g., Zomato/Swiggy)")
    name: str
    age: int = Field(..., ge=18, le=70)
    city: str
    persona: PersonaType
    avg_weekly_orders: int = Field(..., ge=0)
    avg_weekly_earnings: float = Field(..., ge=0)
    historical_cancellations_rate: float = Field(..., ge=0, le=1)


class RiskProfile(BaseModel):
    worker_id: str
    city: Optional[str] = None
    pincode: Optional[str] = None
    avg_daily_income: Optional[float] = None
    platform: Optional[str] = None
    risk_score: float
    risk_band: str
    suggested_weekly_premium: float
    external_frequency_index: Optional[float] = None
    activity_index: Optional[float] = None


class Policy(BaseModel):
    policy_id: str
    worker_id: str
    weekly_premium: float
    coverage_per_week: float
    risk_score: Optional[float] = None
    risk_band: Optional[str] = None
    active: Optional[bool] = True
    created_at: datetime


class DisruptionType(str, Enum):
    ENVIRONMENTAL = "environmental"
    SOCIAL = "social"


class DisruptionEvent(BaseModel):
    event_id: str
    worker_id: str
    disruption_type: DisruptionType
    severity: int = Field(..., ge=1, le=5)
    description: str
    start_time: datetime
    end_time: Optional[datetime] = None


class ClaimStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class Claim(BaseModel):
    claim_id: str
    worker_id: str
    policy_id: str
    event_id: str
    claimed_income_loss: float
    approved_payout: float
    status: ClaimStatus
    created_at: datetime


class AnalyticsMetrics(BaseModel):
    total_workers: int
    active_policies: int
    total_claims: int
    approved_claims: int
    total_payout: float
    avg_risk_score: float
    disruption_counts: List[dict]