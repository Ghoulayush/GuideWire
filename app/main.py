from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .schemas import (
    AnalyticsMetrics,
    Claim,
    ClaimStatus,
    DisruptionEvent,
    DisruptionType,
    Policy,
    RiskProfile,
)
from .services.analytics import build_metrics
from .services.fraud import FraudEngine
from .services.risk import RiskInput, calculate_risk
from .services.triggers import DisruptionInput, evaluate_triggers

app = FastAPI(title="Gig Worker Parametric Insurance Platform")

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class OnboardWorkerRequest(BaseModel):
    worker_id: str
    name: str
    city: str
    pincode: str
    platform: str
    avg_daily_income: float


class OnboardWorkerResponse(BaseModel):
    worker: dict
    risk: RiskProfile
    policy: Policy
    message: str


class TriggerEventRequest(BaseModel):
    worker_id: str
    disruption_type: str
    severity: int = Field(..., ge=1, le=5)
    description: str


class TriggerEventResponse(BaseModel):
    event: DisruptionEvent
    claim: Optional[Claim] = None
    fraud_signals: list = Field(default_factory=list)
    message: str
    triggered: bool


class DashboardResponse(BaseModel):
    policies: list
    claims: list
    metrics: AnalyticsMetrics
    current_worker: Optional[dict] = None
    current_risk: Optional[RiskProfile] = None
    current_policy: Optional[Policy] = None

WORKERS: Dict[str, dict] = {}
RISKS: List[RiskProfile] = []
POLICIES: List[Policy] = []
EVENTS: List[DisruptionEvent] = []
CLAIMS: List[Claim] = []

fraud_engine = FraudEngine()


# REST API Endpoints

@app.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    """Get dashboard with current metrics and latest worker/policy data."""
    metrics: AnalyticsMetrics = build_metrics(RISKS, POLICIES, CLAIMS, EVENTS)
    current_worker = None
    current_risk = None
    current_policy = None

    if WORKERS:
        last_id = list(WORKERS.keys())[-1]
        current_worker = WORKERS[last_id]
        current_risk = next((r for r in RISKS if r.worker_id == last_id), None)
        current_policy = next((p for p in POLICIES if p.worker_id == last_id), None)

    return DashboardResponse(
        policies=POLICIES,
        claims=CLAIMS[-10:],
        metrics=metrics,
        current_worker=current_worker,
        current_risk=current_risk,
        current_policy=current_policy,
    )


@app.post("/workers/onboard", response_model=OnboardWorkerResponse)
async def onboard_worker(request: OnboardWorkerRequest):
    """Onboard a new gig worker, calculate risk, and issue a policy."""
    WORKERS[request.worker_id] = {
        "worker_id": request.worker_id,
        "name": request.name,
        "city": request.city,
        "pincode": request.pincode,
        "platform": request.platform,
        "avg_daily_income": request.avg_daily_income,
    }

    city_lower = request.city.lower()
    external_frequency_index = (
        0.7 if city_lower in {"mumbai", "delhi", "kolkata"} else 0.4
    )
    activity_index = 0.8

    risk_input = RiskInput(
        city=request.city,
        pincode=request.pincode,
        avg_daily_income=request.avg_daily_income,
        platform=request.platform,
        external_frequency_index=external_frequency_index,
        activity_index=activity_index,
    )

    risk = calculate_risk(risk_input)
    risk.worker_id = request.worker_id
    RISKS.append(risk)

    policy = Policy(
        policy_id=str(uuid4()),
        worker_id=request.worker_id,
        weekly_premium=risk.suggested_weekly_premium,
        coverage_per_week=round(request.avg_daily_income * 7 * 0.8, 2),
        created_at=datetime.utcnow(),
    )
    POLICIES.append(policy)

    return OnboardWorkerResponse(
        worker=WORKERS[request.worker_id],
        risk=risk,
        policy=policy,
        message=f"Onboarded {request.name} with risk band {risk.risk_band.upper()} and weekly premium ₹{risk.suggested_weekly_premium}",
    )


@app.post("/events/trigger", response_model=TriggerEventResponse)
async def trigger_event(request: TriggerEventRequest):
    """Trigger a disruption event and evaluate for claim payout."""
    worker = WORKERS.get(request.worker_id)
    if not worker:
        raise ValueError(f"Unknown worker {request.worker_id}. Onboard first.")

    event = DisruptionEvent(
        event_id=str(uuid4()),
        worker_id=request.worker_id,
        disruption_type=DisruptionType(request.disruption_type),
        severity=request.severity,
        description=request.description,
        start_time=datetime.utcnow(),
    )
    EVENTS.append(event)

    avg_daily_income = worker["avg_daily_income"]

    disruption_input = DisruptionInput(
        disruption_type=request.disruption_type,
        severity=request.severity,
        rainfall_mm=request.severity * 15.0,
        heat_index=35 + request.severity * 2,
        aqi=120 + request.severity * 40,
        flood_alert=request.severity >= 4,
        curfew=request.severity >= 4,
    )

    triggered, model_payout = evaluate_triggers(disruption_input, avg_daily_income)

    message = "No payout triggered; event below threshold."
    fraud_signals = []
    claim = None

    if triggered:
        policy = next((p for p in POLICIES if p.worker_id == request.worker_id), None)
        if policy:
            claim = Claim(
                claim_id=str(uuid4()),
                worker_id=request.worker_id,
                policy_id=policy.policy_id,
                event_id=event.event_id,
                claimed_income_loss=model_payout,
                approved_payout=model_payout,
                status=ClaimStatus.APPROVED,
                created_at=datetime.utcnow(),
            )
            fraud_signals = fraud_engine.evaluate_claim(claim)
            if any(s.severity >= 4 for s in fraud_signals):
                claim.status = ClaimStatus.REJECTED
                claim.approved_payout = 0.0
                message = "Claim flagged and rejected by fraud engine."
            else:
                message = f"Auto-claim approved for ₹{model_payout}. Payout initiated."

            CLAIMS.append(claim)
        else:
            message = "No active policy for worker; cannot create claim."

    return TriggerEventResponse(
        event=event,
        claim=claim,
        fraud_signals=fraud_signals,
        message=message,
        triggered=triggered and claim is not None,
    )


@app.get("/analytics/metrics", response_model=AnalyticsMetrics)
async def get_analytics_metrics():
    """Get analytics metrics."""
    return build_metrics(RISKS, POLICIES, CLAIMS, EVENTS)

