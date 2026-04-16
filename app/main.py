from __future__ import annotations

import asyncio
import hmac
import hashlib
import os
import random
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import requests
from dotenv import load_dotenv

load_dotenv()

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

    # Load ML model
    if not risk_model.load_model():
        print("📊 No saved model found. Training new ML model...")
        result = risk_model.train_on_synthetic_data()
        print(f"✅ ML Model trained! Test accuracy: {result['test_score']:.2%}")
    else:
        print("✅ ML Model loaded from disk!")

    # Prevent duplicate background tasks on reload
    if not hasattr(app.state, "monitor_started"):
        app.state.monitor_started = True
        asyncio.create_task(continuous_trigger_monitor())
        print("✅ Background trigger monitoring started (every 30 minutes)")
    else:
        print("✅ Background monitor already running")

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

            for worker_id, worker in WORKERS.items():
                rainfall_mm = random.randint(0, 100)
                aqi = random.randint(50, 400)
                heat_index = random.randint(30, 48)

                # Check if policy is active
                policy = next((p for p in POLICIES if p.worker_id == worker_id), None)
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

    worker = WORKERS.get(worker_id)
    policy = next((p for p in POLICIES if p.worker_id == worker_id), None)

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
        CLAIMS.append(claim)
        return

    claim.status = ClaimStatus.PAID
    claim.approved_payout = payout_amount
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


class TriggerEventResponse(BaseModel):
    event: Optional[DisruptionEvent] = None
    claim: Optional[Claim] = None
    fraud_signals: list = Field(default_factory=list)
    fraud_score: int = 0
    message: str
    triggered: bool
    payout_amount: float = 0


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
        policies=[policy_to_dict(p) for p in POLICIES],
        claims=CLAIMS[-10:],
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

    WORKERS[request.worker_id] = {
        "worker_id": request.worker_id,
        "name": request.name,
        "city": request.city,
        "pincode": request.pincode,
        "platform": request.platform,
        "avg_daily_income": request.avg_daily_income,
        "experience_days": 30,
        "joined_at": datetime.utcnow().isoformat(),
    }

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
    POLICIES.append(policy)

    return OnboardWorkerResponse(
        worker=WORKERS[request.worker_id],
        risk=risk,
        policy=policy,
        message=f"✅ Onboarded {request.name} | Risk: {ml_risk['risk_band']} ({ml_risk['risk_score']:.0f}/100) | Premium: ₹{premium_result['weekly_premium']}/week",
        ml_risk_score=ml_risk["risk_score"],
        weekly_premium=premium_result["weekly_premium"],
    )


@app.post("/events/trigger", response_model=TriggerEventResponse)
async def trigger_event(request: TriggerEventRequest):
    """Trigger a disruption event and evaluate for claim payout."""
    worker = WORKERS.get(request.worker_id)
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

    policy = next((p for p in POLICIES if p.worker_id == request.worker_id), None)
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

    if triggered:
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

        fraud_result = fraud_engine.evaluate_claim(claim)
        fraud_signals = fraud_result.get(
            "reasons", fraud_result.get("legacy_signals", [])
        )
        fraud_score = fraud_result.get("fraud_score", 0)

        print(f"🔍 Fraud analysis: score={fraud_score}/100")

        if fraud_result.get("action") == "REJECT" or fraud_score >= 70:
            claim.status = ClaimStatus.REJECTED
            claim.approved_payout = 0.0
            message = f"🚫 Claim REJECTED by AI Fraud Detection! Fraud score: {fraud_score}/100"
        else:
            claim.status = ClaimStatus.PAID
            message = f"💰 Auto-claim APPROVED! ₹{model_payout} paid to UPI"

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
    )


# ========== DEMO CONTROL ==========
@app.post("/api/simulate/rain")
async def simulate_rain_event(request: SimulateEventRequest):
    """Demo control - simulate rain without waiting for real weather"""
    worker = WORKERS.get(request.worker_id)
    if not worker:
        return {"error": f"Worker {request.worker_id} not found"}

    policy = next((p for p in POLICIES if p.worker_id == request.worker_id), None)
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


# ========== ANALYTICS ENDPOINTS ==========
@app.get("/analytics/metrics", response_model=AnalyticsMetrics)
async def get_analytics_metrics():
    """Get analytics metrics."""
    return build_metrics(RISKS, POLICIES, CLAIMS, EVENTS)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ml_model_loaded": risk_model.is_trained,
        "total_workers": len(WORKERS),
        "total_policies": len(POLICIES),
        "total_claims": len(CLAIMS),
        "background_monitoring": "active",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/fraud/stats")
async def fraud_statistics():
    """Get fraud detection statistics"""
    rejected_claims = [c for c in CLAIMS if c.status == ClaimStatus.REJECTED]
    paid_claims = [c for c in CLAIMS if c.status == ClaimStatus.PAID]

    return {
        "total_claims": len(CLAIMS),
        "approved_claims": len(paid_claims),
        "rejected_claims": len(rejected_claims),
        "fraud_rate": len(rejected_claims) / len(CLAIMS) if CLAIMS else 0,
        "total_payouts": sum(c.approved_payout for c in paid_claims),
        "fraud_prevented": sum(c.claimed_income_loss for c in rejected_claims),
    }


@app.get("/policies")
async def get_policies():
    """Return all policies"""
    return [policy_to_dict(p) for p in POLICIES]


@app.get("/workers")
async def get_workers():
    """Return all workers."""
    return list(WORKERS.values())


@app.get("/claims")
async def get_claims():
    """Return all claims"""
    return [
        {
            "claim_id": c.claim_id,
            "worker_id": c.worker_id,
            "status": c.status.value,
            "approved_payout": c.approved_payout,
        }
        for c in CLAIMS
    ]


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
        SUBSCRIPTIONS.append(
            {
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
        )
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
    SUBSCRIPTIONS.append(
        {
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
    )

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
    record = next(
        (
            s
            for s in reversed(SUBSCRIPTIONS)
            if s.get("order_id") == request.razorpay_order_id
        ),
        None,
    )

    if record and record.get("mode") == "mock":
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
            record["status"] = "FAILED_SIGNATURE"
            record["payment_id"] = request.razorpay_payment_id
        return VerifyRazorpayPaymentResponse(
            status="error",
            verified=False,
            message="Payment signature verification failed.",
        )

    if record:
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
    items = SUBSCRIPTIONS
    if status:
        wanted = status.strip().upper()
        items = [s for s in items if str(s.get("status", "")).upper() == wanted]
    return AllSubscriptionsResponse(total=len(items), items=items)


# ========== RUN SERVER ==========
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
