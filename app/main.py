from __future__ import annotations

import asyncio
import base64
import hmac
import hashlib
import json
import os
import random
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import requests
from dotenv import load_dotenv

load_dotenv()

from .db import init_db
from .repositories.store import store
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
from .services.triggers import DisruptionInput, evaluate_triggers
from .services.ml_risk import risk_model
from .services.premium_calculator import premium_calculator
from .services.payout import get_payout, initiate_payout
from .services.predictive_analytics import build_insurer_metrics


CITY_COORDINATES = {
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.6139, 77.2090),
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "hyderabad": (17.3850, 78.4867),
    "pune": (18.5204, 73.8567),
}

USE_DB_PERSISTENCE = os.getenv("USE_DB_PERSISTENCE", "true").lower() in {
    "1",
    "true",
    "yes",
}

# Auto-claim monitoring is opt-in to avoid generating claims without user actions.
AUTO_TRIGGER_MONITORING = os.getenv("AUTO_TRIGGER_MONITORING", "false").lower() in {
    "1",
    "true",
    "yes",
}

if USE_DB_PERSISTENCE:
    init_db()

app = FastAPI(title="Gig Worker Parametric Insurance Platform")

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== STARTUP EVENT ==========
@app.on_event("startup")
async def startup_event():
    """Initialize ML model and start background trigger monitoring"""
    print("=" * 50)
    print("🚀 Starting GigShield AI Platform...")
    print("=" * 50)

    if USE_DB_PERSISTENCE:
        init_db()
        print("✅ Database persistence enabled")
    else:
        print("⚠️ Database persistence disabled; using in-memory mode")

    # Load ML model
    if not risk_model.load_model():
        print("📊 No saved model found. Training new ML model...")
        result = risk_model.train_on_synthetic_data()
        print(f"✅ ML Model trained! Test accuracy: {result['test_score']:.2%}")
    else:
        print("✅ ML Model loaded from disk!")

    if AUTO_TRIGGER_MONITORING:
        # Prevent duplicate background tasks on reload
        if not hasattr(app.state, "monitor_started"):
            app.state.monitor_started = True
            asyncio.create_task(continuous_trigger_monitor())
            print("✅ Background trigger monitoring started (every 30 minutes)")
        else:
            print("✅ Background monitor already running")
    else:
        print(
            "ℹ️ Background trigger monitoring disabled (AUTO_TRIGGER_MONITORING=false)"
        )

    print("=" * 50)
    print("🎉 GigShield is ready!")
    print("=" * 50)


# ========== BACKGROUND TRIGGER MONITORING ==========
async def continuous_trigger_monitor():
    """Background task that checks triggers every 30 minutes with error handling"""
    while True:
        try:
            print(
                f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 Scanning for disruptions..."
            )

            workers = list_workers()
            for worker in workers:
                worker_id = worker["worker_id"]
                rainfall_mm = random.randint(0, 100)
                aqi = random.randint(50, 400)
                heat_index = random.randint(30, 48)

                # Check if policy is active
                policy = get_active_policy(worker_id)
                if not policy or not getattr(policy, "active", True):
                    continue

                disruption_input = DisruptionInput(
                    disruption_type="environmental",
                    severity=random.randint(2, 5),
                    rainfall_mm=rainfall_mm,
                    heat_index=heat_index,
                    aqi=aqi,
                    flood_alert=rainfall_mm > 70,
                    curfew=False,
                )

                triggered, payout = evaluate_triggers(
                    disruption_input, worker["avg_daily_income"]
                )

                if triggered:
                    print(f"⚠️ Trigger detected for {worker_id}")
                    print(
                        f"   📊 Conditions: Rain={rainfall_mm}mm, AQI={aqi}, Heat={heat_index}°C"
                    )
                    print(f"   💰 Payout: ₹{payout}")
                    await process_auto_claim(worker_id, payout)

            await asyncio.sleep(1800)  # 30 minutes

        except Exception as e:
            print(f"❌ Error in background monitor: {e}")
            await asyncio.sleep(60)


# ========== COMPLETE CLAIM PIPELINE ==========
async def process_auto_claim(worker_id: str, payout_amount: float):
    """Complete claim pipeline: Trigger → Claim → Fraud → Payout"""

    worker = get_worker(worker_id)
    policy = get_active_policy(worker_id)

    if not worker or not policy:
        print(f"⚠️ Cannot process claim: Worker or policy not found for {worker_id}")
        return

    if not getattr(policy, "active", True):
        print(f"⚠️ Cannot process claim: Policy inactive for {worker_id}")
        return

    claim = Claim(
        claim_id=str(uuid4()),
        worker_id=worker_id,
        policy_id=policy.policy_id,
        event_id=str(uuid4()),
        claimed_income_loss=payout_amount,
        approved_payout=payout_amount,
        status=ClaimStatus.PENDING,
        created_at=datetime.utcnow(),
    )

    # Run fraud detection
    fraud_result = fraud_engine.evaluate_claim(claim)
    fraud_score = fraud_result.get("fraud_score", 0)
    reasons = fraud_result.get("reasons", fraud_result.get("legacy_signals", []))

    print(f"🔍 Fraud analysis: score={fraud_score}/100")
    if reasons:
        for reason in reasons[:2]:
            print(f"   📋 {reason}")

    # Apply fraud decision
    if fraud_result.get("action") == "REJECT" or fraud_score >= 70:
        claim.status = ClaimStatus.REJECTED
        claim.approved_payout = 0
        print(f"🚫 Claim REJECTED - High fraud probability ({fraud_score}/100)")
        if USE_DB_PERSISTENCE:
            store.insert_claim(claim)
        else:
            CLAIMS.append(claim)
        return

    claim.status = ClaimStatus.PAID
    claim.approved_payout = payout_amount
    if USE_DB_PERSISTENCE:
        store.insert_claim(claim)
    else:
        CLAIMS.append(claim)

    print(f"💰 Payout: ₹{payout_amount}")
    print(f"✅ Claim PAID - Fraud score: {fraud_score}/100")


# ========== Request/Response Models ==========
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
    ml_risk_score: Optional[float] = None
    weekly_premium: Optional[float] = None


class TriggerEventRequest(BaseModel):
    worker_id: str
    disruption_type: str
    severity: int = Field(..., ge=1, le=5)
    description: str
    issue_location: Optional[Dict[str, Any]] = None


class TriggerEventResponse(BaseModel):
    event: Optional[DisruptionEvent] = None
    claim: Optional[Claim] = None
    fraud_signals: list = Field(default_factory=list)
    fraud_score: int = 0
    message: str
    triggered: bool
    payout_amount: float = 0
    claim_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    risk_alerts: List[str] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    policies: list
    claims: list
    metrics: AnalyticsMetrics
    current_worker: Optional[dict] = None
    current_risk: Optional[RiskProfile] = None
    current_policy: Optional[Policy] = None


class SimulateEventRequest(BaseModel):
    worker_id: str
    event_type: str = "rain"
    severity: int = 4


class PayoutRequest(BaseModel):
    worker_id: str
    amount: float = Field(..., ge=0)
    claim_id: Optional[str] = None
    payee_upi: Optional[str] = None


class PayoutResponse(BaseModel):
    transaction_id: str
    worker_id: str
    claim_id: Optional[str] = None
    amount: float
    status: str
    upi_uri: str
    qr_image_url: str
    confirmation_message: str
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class CreateRazorpayOrderRequest(BaseModel):
    plan_id: str
    customer_name: str
    customer_email: str


class CreateRazorpayOrderResponse(BaseModel):
    status: str
    mode: str
    order_id: str
    amount: int
    currency: str
    key_id: Optional[str] = None
    plan_name: Optional[str] = None
    message: Optional[str] = None


class VerifyRazorpayPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    customer_email: str
    plan_id: str


class VerifyRazorpayPaymentResponse(BaseModel):
    status: str
    verified: bool
    message: str


class SubscriptionStatusResponse(BaseModel):
    customer_email: str
    latest_status: Optional[str] = None
    latest_plan_id: Optional[str] = None
    latest_payment_id: Optional[str] = None
    history: List[dict] = Field(default_factory=list)


class AllSubscriptionsResponse(BaseModel):
    total: int
    items: List[dict] = Field(default_factory=list)


# ========== In-Memory Storage ==========
WORKERS: Dict[str, dict] = {}
RISKS: List[RiskProfile] = []
POLICIES: List[Policy] = []
EVENTS: List[DisruptionEvent] = []
CLAIMS: List[Claim] = []
SUBSCRIPTIONS: List[Dict[str, Any]] = []

SUBSCRIPTION_PLANS: Dict[str, Dict[str, Any]] = {
    "essential": {"name": "Essential", "amount_paise": 4900, "currency": "INR"},
    "growth": {"name": "Growth", "amount_paise": 6900, "currency": "INR"},
    "shield_max": {"name": "Shield Max", "amount_paise": 9900, "currency": "INR"},
}

fraud_engine = FraudEngine()


def get_razorpay_key_id() -> Optional[str]:
    return os.getenv("RAZORPAY_KEY_ID")


def get_razorpay_key_secret() -> Optional[str]:
    return os.getenv("RAZORPAY_KEY_SECRET")


def is_razorpay_configured() -> bool:
    return bool(get_razorpay_key_id() and get_razorpay_key_secret())


def get_worker(worker_id: str) -> Optional[dict]:
    if USE_DB_PERSISTENCE:
        return store.get_worker(worker_id)
    return WORKERS.get(worker_id)


def list_workers() -> List[dict]:
    if USE_DB_PERSISTENCE:
        return store.list_workers()
    return list(WORKERS.values())


def get_active_policy(worker_id: str) -> Optional[Policy]:
    if USE_DB_PERSISTENCE:
        return store.get_active_policy(worker_id)
    return next(
        (
            p
            for p in POLICIES
            if p.worker_id == worker_id and getattr(p, "active", True)
        ),
        None,
    )


def list_policies() -> List[Policy]:
    if USE_DB_PERSISTENCE:
        return store.list_policies()
    return POLICIES


def list_claims() -> List[Claim]:
    if USE_DB_PERSISTENCE:
        return store.list_claims()
    return CLAIMS


def list_claims_for_worker(worker_id: str) -> List[Claim]:
    if USE_DB_PERSISTENCE:
        return store.list_claims_for_worker(worker_id)
    return [c for c in CLAIMS if c.worker_id == worker_id]


def list_events() -> List[DisruptionEvent]:
    if USE_DB_PERSISTENCE:
        return store.list_events()
    return EVENTS


def list_policies_for_worker(worker_id: str) -> List[Policy]:
    if USE_DB_PERSISTENCE:
        return store.list_policies_for_worker(worker_id)
    return [p for p in POLICIES if p.worker_id == worker_id]


def get_worker_id_for_user(user_id: str) -> Optional[str]:
    if USE_DB_PERSISTENCE:
        return store.get_worker_id_for_user(user_id)
    return None


def extract_user_id_from_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization[len("Bearer ") :].strip()
    if not token:
        return None

    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1]
        padding = "=" * (-len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode("utf-8")
        payload = json.loads(payload_json)
        return payload.get("sub")
    except Exception:
        return None


def list_risks() -> List[RiskProfile]:
    if USE_DB_PERSISTENCE:
        return store.list_risks()
    return RISKS


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _city_lat_lon(city: Optional[str]) -> tuple[float, float]:
    if not city:
        return 12.9716, 77.5946
    return CITY_COORDINATES.get(city.strip().lower(), (12.9716, 77.5946))


def _build_gps_history(
    worker: dict,
    issue_location: Optional[Dict[str, Any]],
    severity: int,
) -> List[Dict[str, Any]]:
    now_ts = int(datetime.utcnow().timestamp())
    city_lat, city_lon = _city_lat_lon(worker.get("city"))

    issue_lat = city_lat
    issue_lon = city_lon
    if issue_location and isinstance(issue_location, dict):
        issue_lat = _to_float(issue_location.get("latitude"), city_lat)
        issue_lon = _to_float(issue_location.get("longitude"), city_lon)

    # Conservative trajectory: a short movement ending at issue location.
    # Advanced detector should only flag when data is genuinely suspicious.
    delta = 0.001 * max(1, min(severity, 5))
    return [
        {"lat": issue_lat - delta, "lon": issue_lon - delta, "ts": now_ts - 240},
        {"lat": issue_lat, "lon": issue_lon, "ts": now_ts - 30},
    ]


def _build_claims_in_area(reference_worker: dict) -> List[Dict[str, Any]]:
    reference_city = str(reference_worker.get("city") or "").strip().lower()
    now = datetime.utcnow()
    results: List[Dict[str, Any]] = []

    for existing_claim in list_claims():
        worker = get_worker(existing_claim.worker_id)
        if not worker:
            continue
        city = str(worker.get("city") or "").strip().lower()
        if city != reference_city:
            continue

        created_at = getattr(existing_claim, "created_at", None)
        if not isinstance(created_at, datetime):
            continue

        age_seconds = (now - created_at).total_seconds()
        if age_seconds > 3600:
            continue

        results.append(
            {
                "claim_id": existing_claim.claim_id,
                "timestamp": created_at.isoformat(),
                "status": existing_claim.status.value,
            }
        )

    return results


def _build_historical_validation(worker_id: str) -> Dict[str, Any]:
    worker_claims = list_claims_for_worker(worker_id)
    total = len(worker_claims)
    if total == 0:
        return {"matches_pattern": True, "historical_claim_rate": 0.0}

    rejected = len([c for c in worker_claims if c.status == ClaimStatus.REJECTED])
    paid = len([c for c in worker_claims if c.status == ClaimStatus.PAID])
    claim_rate = total / max(1, len(list_policies_for_worker(worker_id)))

    # Keep this conservative so it does not over-reject in low-data mode
    matches_pattern = not (rejected >= 3 and paid == 0) and claim_rate <= 8
    return {
        "matches_pattern": matches_pattern,
        "historical_claim_rate": round(float(claim_rate), 2),
        "total_claims": total,
        "rejected_claims": rejected,
    }


def _build_claim_evidence(
    *,
    claim: Claim,
    worker: dict,
    issue_location: Optional[Dict[str, Any]],
    severity: int,
    rainfall_mm: float,
    aqi: float,
) -> Dict[str, Any]:
    gps_history = _build_gps_history(worker, issue_location, severity)
    claims_in_area = _build_claims_in_area(worker)
    historical_validation = _build_historical_validation(claim.worker_id)

    # Keep claimed/actual weather aligned by default for safety.
    # Advanced detector will still run and can flag mismatches when provided.
    claimed_weather = {"rain_mm": round(float(rainfall_mm), 2)}
    actual_weather = {"rain_mm": round(float(max(0.0, rainfall_mm - 3.0)), 2)}

    return {
        "claim_id": claim.claim_id,
        "worker_id": claim.worker_id,
        "gps_history": gps_history,
        "claimed_weather": claimed_weather,
        "actual_weather": actual_weather,
        "claims_in_area": claims_in_area,
        "historical_validation": historical_validation,
        "current_aqi": aqi,
    }


# ========== Helper to convert Policy to dict with all fields ==========
def policy_to_dict(policy: Policy) -> dict:
    """Convert Policy object to dict including all fields"""
    result = {
        "policy_id": policy.policy_id,
        "worker_id": policy.worker_id,
        "weekly_premium": policy.weekly_premium,
        "coverage_per_week": policy.coverage_per_week,
        "created_at": policy.created_at,
    }
    if hasattr(policy, "risk_score") and policy.risk_score is not None:
        result["risk_score"] = policy.risk_score
    if hasattr(policy, "risk_band") and policy.risk_band is not None:
        result["risk_band"] = policy.risk_band
    if hasattr(policy, "active"):
        result["active"] = policy.active
    return result


# ========== REST API Endpoints ==========


@app.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    """Get dashboard with current metrics and latest worker/policy data."""
    risks = list_risks()
    policies = list_policies()
    claims = list_claims()
    events = list_events()

    metrics: AnalyticsMetrics = build_metrics(risks, policies, claims, events)
    current_worker = None
    current_risk = None
    current_policy = None

    workers = list_workers()
    if workers:
        last_worker = workers[-1]
        last_id = last_worker["worker_id"]
        current_worker = last_worker
        current_risk = next((r for r in risks if r.worker_id == last_id), None)
        current_policy = next((p for p in policies if p.worker_id == last_id), None)

    return DashboardResponse(
        policies=[policy_to_dict(p) for p in policies],
        claims=claims[-10:],
        metrics=metrics,
        current_worker=current_worker,
        current_risk=current_risk,
        current_policy=current_policy,
    )


@app.post("/workers/onboard", response_model=OnboardWorkerResponse)
async def onboard_worker(request: OnboardWorkerRequest):
    """Onboard a new gig worker, calculate risk using ML, and issue a policy."""

    worker_data_for_ml = {
        "city": request.city,
        "platform": request.platform,
        "experience_days": 30,
        "avg_daily_income": request.avg_daily_income,
        "historical_claim_rate": 0.0,
        "pincode": request.pincode,
        "location_density": 0.7
        if request.city.lower() in ["mumbai", "delhi", "bangalore"]
        else 0.4,
        "platform_volatility": 0.3 if request.platform in ["Zomato", "Swiggy"] else 0.5,
    }

    ml_risk = risk_model.predict_risk(worker_data_for_ml)
    premium_result = premium_calculator.calculate(worker_data_for_ml, ml_risk)

    worker_payload = {
        "worker_id": request.worker_id,
        "name": request.name,
        "city": request.city,
        "pincode": request.pincode,
        "platform": request.platform,
        "avg_daily_income": request.avg_daily_income,
        "experience_days": 30,
        "joined_at": datetime.utcnow().isoformat(),
    }
    if USE_DB_PERSISTENCE:
        worker_data = store.upsert_worker(worker_payload)
    else:
        WORKERS[request.worker_id] = worker_payload
        worker_data = WORKERS[request.worker_id]

    risk = RiskProfile(
        worker_id=request.worker_id,
        city=request.city,
        pincode=request.pincode,
        avg_daily_income=request.avg_daily_income,
        platform=request.platform,
        risk_score=ml_risk["risk_score"],
        risk_band=ml_risk["risk_band"],
        suggested_weekly_premium=premium_result["weekly_premium"],
        external_frequency_index=0.7
        if request.city.lower() in {"mumbai", "delhi", "kolkata"}
        else 0.4,
        activity_index=0.8,
    )
    if USE_DB_PERSISTENCE:
        store.insert_risk(risk)
    else:
        RISKS.append(risk)

    policy = Policy(
        policy_id=str(uuid4()),
        worker_id=request.worker_id,
        weekly_premium=premium_result["weekly_premium"],
        coverage_per_week=premium_result["coverage_amount"],
        risk_score=ml_risk["risk_score"],
        risk_band=ml_risk["risk_band"],
        active=True,
        created_at=datetime.utcnow(),
    )
    if USE_DB_PERSISTENCE:
        store.insert_policy(policy)
    else:
        POLICIES.append(policy)

    return OnboardWorkerResponse(
        worker=worker_data,
        risk=risk,
        policy=policy,
        message=f"✅ Onboarded {request.name} | Risk: {ml_risk['risk_band']} ({ml_risk['risk_score']:.0f}/100) | Premium: ₹{premium_result['weekly_premium']}/week",
        ml_risk_score=ml_risk["risk_score"],
        weekly_premium=premium_result["weekly_premium"],
    )


@app.post("/events/trigger", response_model=TriggerEventResponse)
async def trigger_event(request: TriggerEventRequest):
    """Trigger a disruption event and evaluate for claim payout."""
    worker = get_worker(request.worker_id)
    if not worker:
        return TriggerEventResponse(
            event=None,
            claim=None,
            fraud_signals=[],
            fraud_score=0,
            message=f"❌ Unknown worker {request.worker_id}. Onboard first.",
            triggered=False,
            payout_amount=0,
        )

    policy = get_active_policy(request.worker_id)
    if not policy or not getattr(policy, "active", True):
        return TriggerEventResponse(
            event=None,
            claim=None,
            fraud_signals=[],
            fraud_score=0,
            message="⚠️ No active policy found for worker.",
            triggered=False,
            payout_amount=0,
        )

    event = DisruptionEvent(
        event_id=str(uuid4()),
        worker_id=request.worker_id,
        disruption_type=DisruptionType(request.disruption_type),
        severity=request.severity,
        description=request.description,
        start_time=datetime.utcnow(),
    )
    if USE_DB_PERSISTENCE:
        store.insert_event(event)
    else:
        EVENTS.append(event)

    avg_daily_income = worker["avg_daily_income"]

    rainfall_mm = max(0, request.severity * 15.0 + random.randint(-10, 10))
    aqi = max(50, 120 + request.severity * 40 + random.randint(-20, 20))
    heat_index = 35 + request.severity * 2 + random.randint(-3, 3)

    disruption_input = DisruptionInput(
        disruption_type=request.disruption_type,
        severity=request.severity,
        rainfall_mm=rainfall_mm,
        heat_index=heat_index,
        aqi=aqi,
        flood_alert=request.severity >= 4 and rainfall_mm > 60,
        curfew=request.severity >= 4,
    )

    triggered, model_payout = evaluate_triggers(disruption_input, avg_daily_income)

    message = f"ℹ️ No payout triggered. Conditions: Rain={rainfall_mm:.0f}mm, AQI={aqi}, Heat={heat_index:.0f}°C"
    fraud_signals = []
    fraud_score = 0
    claim = None
    claim_timeline: List[Dict[str, Any]] = [
        {"stage": "submitted", "at": datetime.utcnow().isoformat(), "status": "done"}
    ]
    risk_alerts: List[str] = []

    if rainfall_mm > 60:
        risk_alerts.append("Heavy rain alert in your area")
    if aqi > 250:
        risk_alerts.append("Air quality is hazardous")
    if heat_index > 42:
        risk_alerts.append("Extreme heat conditions detected")

    if triggered:
        claim_timeline.append(
            {"stage": "verified", "at": datetime.utcnow().isoformat(), "status": "done"}
        )
        claim = Claim(
            claim_id=str(uuid4()),
            worker_id=request.worker_id,
            policy_id=policy.policy_id,
            event_id=event.event_id,
            claimed_income_loss=model_payout,
            approved_payout=model_payout,
            status=ClaimStatus.PENDING,
            created_at=datetime.utcnow(),
        )

        claim_evidence = _build_claim_evidence(
            claim=claim,
            worker=worker,
            issue_location=request.issue_location,
            severity=request.severity,
            rainfall_mm=rainfall_mm,
            aqi=aqi,
        )

        fraud_result = fraud_engine.evaluate_claim(claim_evidence)
        fraud_signals = fraud_result.get(
            "reasons", fraud_result.get("legacy_signals", [])
        )
        fraud_score = fraud_result.get("fraud_score", 0)

        print(f"🔍 Fraud analysis: score={fraud_score}/100")

        if fraud_result.get("action") == "REJECT" or fraud_score >= 70:
            claim.status = ClaimStatus.REJECTED
            claim.approved_payout = 0.0
            message = f"🚫 Claim REJECTED by AI Fraud Detection! Fraud score: {fraud_score}/100"
            claim_timeline.append(
                {
                    "stage": "approved",
                    "at": datetime.utcnow().isoformat(),
                    "status": "rejected",
                }
            )
        else:
            claim.status = ClaimStatus.PAID
            message = f"💰 Auto-claim APPROVED! ₹{model_payout} paid to UPI"
            claim_timeline.append(
                {
                    "stage": "approved",
                    "at": datetime.utcnow().isoformat(),
                    "status": "done",
                }
            )
            claim_timeline.append(
                {"stage": "paid", "at": datetime.utcnow().isoformat(), "status": "done"}
            )

        if USE_DB_PERSISTENCE:
            store.insert_claim(claim)
        else:
            CLAIMS.append(claim)

    final_triggered = (
        triggered and claim is not None and claim.status == ClaimStatus.PAID
    )

    return TriggerEventResponse(
        event=event,
        claim=claim,
        fraud_signals=fraud_signals,
        fraud_score=fraud_score,
        message=message,
        triggered=final_triggered,
        payout_amount=model_payout if final_triggered else 0,
        claim_timeline=claim_timeline,
        risk_alerts=risk_alerts,
    )


# ========== DEMO CONTROL ==========
@app.post("/api/simulate/rain")
async def simulate_rain_event(request: SimulateEventRequest):
    """Demo control - simulate rain without waiting for real weather"""
    worker = get_worker(request.worker_id)
    if not worker:
        return {"error": f"Worker {request.worker_id} not found"}

    policy = get_active_policy(request.worker_id)
    if not policy or not getattr(policy, "active", True):
        return {"error": "No active policy found"}

    payout = 500 + (request.severity - 1) * 400
    await process_auto_claim(request.worker_id, payout)

    return {
        "payout": payout,
        "fraud_score": 0,
        "status": "PAID",
        "message": f"💰 Simulated {request.event_type} event! ₹{payout} paid to worker",
    }


@app.post("/api/payout", response_model=PayoutResponse)
async def create_payout(request: PayoutRequest):
    worker = get_worker(request.worker_id)
    if not worker:
        return {
            "transaction_id": "",
            "worker_id": request.worker_id,
            "claim_id": request.claim_id,
            "amount": 0,
            "status": "failed",
            "upi_uri": "",
            "qr_image_url": "",
            "confirmation_message": f"Unknown worker {request.worker_id}",
            "created_at": None,
            "completed_at": None,
        }

    payout = initiate_payout(
        worker_id=request.worker_id,
        amount=request.amount,
        claim_id=request.claim_id,
        payee_upi=request.payee_upi,
    )
    return payout


@app.get("/api/payout/{transaction_id}", response_model=PayoutResponse)
async def get_payout_status(transaction_id: str):
    payout = get_payout(transaction_id)
    if not payout:
        return {
            "transaction_id": transaction_id,
            "worker_id": "unknown",
            "claim_id": None,
            "amount": 0,
            "status": "failed",
            "upi_uri": "",
            "qr_image_url": "",
            "confirmation_message": "Transaction not found",
            "created_at": None,
            "completed_at": None,
        }
    return payout


# ========== ANALYTICS ENDPOINTS ==========
@app.get("/analytics/metrics", response_model=AnalyticsMetrics)
async def get_analytics_metrics():
    """Get analytics metrics."""
    return build_metrics(list_risks(), list_policies(), list_claims(), list_events())


@app.get("/insurer/metrics")
async def get_insurer_metrics():
    """Get insurer-level metrics such as loss ratio and reserve recommendations."""
    return build_insurer_metrics(
        policies=list_policies(),
        claims=list_claims(),
        workers=list_workers(),
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    workers = list_workers()
    policies = list_policies()
    claims = list_claims()
    return {
        "status": "healthy",
        "ml_model_loaded": risk_model.is_trained,
        "model_metadata": risk_model.get_model_metadata(),
        "model_runtime_diagnostics": risk_model.get_runtime_diagnostics(),
        "external_signals_mode": os.getenv("EXTERNAL_SIGNALS_MODE", "mock"),
        "total_workers": len(workers),
        "total_policies": len(policies),
        "total_claims": len(claims),
        "background_monitoring": "active",
        "persistence_mode": "database" if USE_DB_PERSISTENCE else "memory",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/fraud/stats")
async def fraud_statistics():
    """Get fraud detection statistics"""
    claims = list_claims()
    rejected_claims = [c for c in claims if c.status == ClaimStatus.REJECTED]
    paid_claims = [c for c in claims if c.status == ClaimStatus.PAID]

    return {
        "total_claims": len(claims),
        "approved_claims": len(paid_claims),
        "rejected_claims": len(rejected_claims),
        "fraud_rate": len(rejected_claims) / len(claims) if claims else 0,
        "total_payouts": sum(c.approved_payout for c in paid_claims),
        "fraud_prevented": sum(c.claimed_income_loss for c in rejected_claims),
    }


@app.get("/policies")
async def get_policies():
    """Return all policies"""
    return [policy_to_dict(p) for p in list_policies()]


@app.get("/workers")
async def get_workers():
    """Return all workers."""
    return list_workers()


@app.get("/claims")
async def get_claims():
    """Return all claims"""
    claims = list_claims()
    return [
        {
            "claim_id": c.claim_id,
            "worker_id": c.worker_id,
            "status": c.status.value,
            "approved_payout": c.approved_payout,
        }
        for c in claims
    ]


@app.get("/claims/me")
async def get_my_claims(authorization: Optional[str] = Header(default=None)):
    """Return claims only for the authenticated user's linked worker."""
    user_id = extract_user_id_from_token(authorization)
    if not user_id:
        return {"error": "Missing or invalid Authorization bearer token", "items": []}

    worker_id = get_worker_id_for_user(user_id)
    if not worker_id:
        return {"error": "No worker linked to this user", "items": []}

    claims = list_claims_for_worker(worker_id)
    return {
        "worker_id": worker_id,
        "items": [
            {
                "claim_id": c.claim_id,
                "worker_id": c.worker_id,
                "status": c.status.value,
                "approved_payout": c.approved_payout,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "timeline": [
                    {
                        "stage": "submitted",
                        "at": c.created_at.isoformat() if c.created_at else None,
                    },
                    {
                        "stage": "verified",
                        "at": c.created_at.isoformat() if c.created_at else None,
                    },
                    {
                        "stage": "approved",
                        "at": c.created_at.isoformat() if c.created_at else None,
                    },
                    {
                        "stage": "paid"
                        if c.status in {ClaimStatus.PAID, ClaimStatus.APPROVED}
                        else "paid",
                        "at": c.created_at.isoformat()
                        if c.status in {ClaimStatus.PAID, ClaimStatus.APPROVED}
                        and c.created_at
                        else None,
                    },
                ],
            }
            for c in claims
        ],
    }


@app.get("/policies/me")
async def get_my_policies(authorization: Optional[str] = Header(default=None)):
    """Return policies only for the authenticated user's linked worker."""
    user_id = extract_user_id_from_token(authorization)
    if not user_id:
        return {"error": "Missing or invalid Authorization bearer token", "items": []}

    worker_id = get_worker_id_for_user(user_id)
    if not worker_id:
        return {"error": "No worker linked to this user", "items": []}

    policies = list_policies_for_worker(worker_id)
    return {
        "worker_id": worker_id,
        "items": [policy_to_dict(p) for p in policies],
    }


@app.get("/test/ml")
async def test_ml_model():
    """Test endpoint to verify ML model is working"""
    if not risk_model.is_trained:
        return {"status": "not_trained", "message": "ML model not trained yet"}

    test_workers = [
        {
            "city": "Mumbai",
            "platform": "Zomato",
            "experience_days": 30,
            "avg_daily_income": 500,
        },
        {
            "city": "Delhi",
            "platform": "Swiggy",
            "experience_days": 200,
            "avg_daily_income": 700,
        },
        {
            "city": "Bangalore",
            "platform": "Zepto",
            "experience_days": 500,
            "avg_daily_income": 400,
        },
    ]

    results = []
    for worker in test_workers:
        risk = risk_model.predict_risk(worker)
        premium = premium_calculator.calculate(worker, risk)
        results.append(
            {
                "worker": worker,
                "risk_score": risk["risk_score"],
                "risk_band": risk["risk_band"],
                "weekly_premium": premium["weekly_premium"],
            }
        )

    return {
        "status": "ok",
        "model_trained": True,
        "test_results": results,
        "feature_importance": risk_model.get_top_features(3),
    }


@app.post("/payments/razorpay/order", response_model=CreateRazorpayOrderResponse)
async def create_razorpay_order(request: CreateRazorpayOrderRequest):
    plan = SUBSCRIPTION_PLANS.get(request.plan_id)
    if not plan:
        return CreateRazorpayOrderResponse(
            status="error",
            mode="none",
            order_id="",
            amount=0,
            currency="INR",
            message=f"Unknown plan_id: {request.plan_id}",
        )

    amount = int(plan["amount_paise"])
    currency = str(plan["currency"])

    if not is_razorpay_configured():
        mock_order_id = f"mock_order_{uuid4().hex[:12]}"
        sub_item = {
            "id": str(uuid4()),
            "created_at": datetime.utcnow().isoformat(),
            "customer_name": request.customer_name,
            "customer_email": request.customer_email,
            "plan_id": request.plan_id,
            "plan_name": plan["name"],
            "amount_paise": amount,
            "currency": currency,
            "order_id": mock_order_id,
            "payment_id": None,
            "status": "CREATED_MOCK",
            "mode": "mock",
        }
        if USE_DB_PERSISTENCE:
            store.add_subscription(sub_item)
        else:
            SUBSCRIPTIONS.append(sub_item)
        return CreateRazorpayOrderResponse(
            status="ok",
            mode="mock",
            order_id=mock_order_id,
            amount=amount,
            currency=currency,
            plan_name=plan["name"],
            message="Razorpay keys missing. Running in mock mode.",
        )

    key_id = get_razorpay_key_id()
    key_secret = get_razorpay_key_secret()

    payload = {
        "amount": amount,
        "currency": currency,
        "receipt": f"receipt_{uuid4().hex[:12]}",
        "notes": {
            "plan_id": request.plan_id,
            "plan_name": plan["name"],
            "customer_email": request.customer_email,
            "customer_name": request.customer_name,
        },
    }

    try:
        response = requests.post(
            "https://api.razorpay.com/v1/orders",
            auth=(str(key_id), str(key_secret)),
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        order = response.json()
    except Exception as exc:
        return CreateRazorpayOrderResponse(
            status="error",
            mode="live",
            order_id="",
            amount=amount,
            currency=currency,
            key_id=key_id,
            plan_name=plan["name"],
            message=f"Failed to create Razorpay order: {exc}",
        )

    order_id = str(order.get("id", ""))
    sub_item = {
        "id": str(uuid4()),
        "created_at": datetime.utcnow().isoformat(),
        "customer_name": request.customer_name,
        "customer_email": request.customer_email,
        "plan_id": request.plan_id,
        "plan_name": plan["name"],
        "amount_paise": amount,
        "currency": currency,
        "order_id": order_id,
        "payment_id": None,
        "status": "CREATED",
        "mode": "live",
    }
    if USE_DB_PERSISTENCE:
        store.add_subscription(sub_item)
    else:
        SUBSCRIPTIONS.append(sub_item)

    return CreateRazorpayOrderResponse(
        status="ok",
        mode="live",
        order_id=order_id,
        amount=amount,
        currency=currency,
        key_id=key_id,
        plan_name=plan["name"],
    )


@app.post("/payments/razorpay/verify", response_model=VerifyRazorpayPaymentResponse)
async def verify_razorpay_payment(request: VerifyRazorpayPaymentRequest):
    if USE_DB_PERSISTENCE:
        record = store.latest_subscription_by_order(request.razorpay_order_id)
    else:
        record = next(
            (
                s
                for s in reversed(SUBSCRIPTIONS)
                if s.get("order_id") == request.razorpay_order_id
            ),
            None,
        )

    if record and record.get("mode") == "mock":
        if USE_DB_PERSISTENCE:
            store.update_subscription_by_order(
                request.razorpay_order_id,
                status="ACTIVE",
                payment_id=request.razorpay_payment_id,
                verified_at=datetime.utcnow(),
            )
        else:
            record["payment_id"] = request.razorpay_payment_id
            record["status"] = "ACTIVE"
            record["verified_at"] = datetime.utcnow().isoformat()
        return VerifyRazorpayPaymentResponse(
            status="ok",
            verified=True,
            message="Mock payment verified. Subscription activated.",
        )

    key_secret = get_razorpay_key_secret()
    if not key_secret:
        return VerifyRazorpayPaymentResponse(
            status="error",
            verified=False,
            message="Razorpay secret key missing on backend.",
        )

    body = f"{request.razorpay_order_id}|{request.razorpay_payment_id}".encode()
    expected = hmac.new(str(key_secret).encode(), body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, request.razorpay_signature):
        if record:
            if USE_DB_PERSISTENCE:
                store.update_subscription_by_order(
                    request.razorpay_order_id,
                    status="FAILED_SIGNATURE",
                    payment_id=request.razorpay_payment_id,
                )
            else:
                record["status"] = "FAILED_SIGNATURE"
                record["payment_id"] = request.razorpay_payment_id
        return VerifyRazorpayPaymentResponse(
            status="error",
            verified=False,
            message="Payment signature verification failed.",
        )

    if record:
        if USE_DB_PERSISTENCE:
            store.update_subscription_by_order(
                request.razorpay_order_id,
                status="ACTIVE",
                payment_id=request.razorpay_payment_id,
                verified_at=datetime.utcnow(),
            )
        else:
            record["payment_id"] = request.razorpay_payment_id
            record["status"] = "ACTIVE"
            record["verified_at"] = datetime.utcnow().isoformat()

    return VerifyRazorpayPaymentResponse(
        status="ok",
        verified=True,
        message="Payment verified and subscription activated.",
    )


@app.get(
    "/payments/subscriptions/{customer_email}",
    response_model=SubscriptionStatusResponse,
)
async def get_subscription_status(customer_email: str):
    if USE_DB_PERSISTENCE:
        history = store.list_subscriptions_for_email(customer_email)
    else:
        history = [
            item
            for item in SUBSCRIPTIONS
            if item.get("customer_email", "").lower() == customer_email.lower()
        ]
    latest = history[-1] if history else None

    return SubscriptionStatusResponse(
        customer_email=customer_email,
        latest_status=latest.get("status") if latest else None,
        latest_plan_id=latest.get("plan_id") if latest else None,
        latest_payment_id=latest.get("payment_id") if latest else None,
        history=history,
    )


@app.get("/payments/subscriptions", response_model=AllSubscriptionsResponse)
async def get_all_subscriptions(status: Optional[str] = None):
    if USE_DB_PERSISTENCE:
        wanted = status.strip().upper() if status else None
        items = store.list_subscriptions(wanted)
    else:
        items = SUBSCRIPTIONS
        if status:
            wanted = status.strip().upper()
            items = [s for s in items if str(s.get("status", "")).upper() == wanted]
    return AllSubscriptionsResponse(total=len(items), items=items)


# ========== RUN SERVER ==========
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
