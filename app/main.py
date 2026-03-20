from __future__ import annotations

from datetime import datetime
from typing import Dict, List
from uuid import uuid4

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")


WORKERS: Dict[str, dict] = {}
RISKS: List[RiskProfile] = []
POLICIES: List[Policy] = []
EVENTS: List[DisruptionEvent] = []
CLAIMS: List[Claim] = []

fraud_engine = FraudEngine()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    metrics: AnalyticsMetrics = build_metrics(RISKS, POLICIES, CLAIMS, EVENTS)
    current_worker = None
    current_risk = None
    current_policy = None
    if WORKERS:
        last_id = list(WORKERS.keys())[-1]
        current_worker = WORKERS[last_id]
        current_risk = next((r for r in RISKS if r.worker_id == last_id), None)
        current_policy = next((p for p in POLICIES if p.worker_id == last_id), None)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "policies": POLICIES,
            "claims": CLAIMS[-10:],
            "metrics": metrics,
            "current_worker": current_worker,
            "current_risk": current_risk,
            "current_policy": current_policy,
        },
    )


@app.post("/onboard", response_class=HTMLResponse)
async def onboard_worker(
    request: Request,
    worker_id: str = Form(...),
    name: str = Form(...),
    city: str = Form(...),
    pincode: str = Form(...),
    platform: str = Form(...),
    avg_daily_income: float = Form(...),
):
    WORKERS[worker_id] = {
        "worker_id": worker_id,
        "name": name,
        "city": city,
        "pincode": pincode,
        "platform": platform,
        "avg_daily_income": avg_daily_income,
    }

    city_lower = city.lower()
    external_frequency_index = 0.7 if city_lower in {"mumbai", "delhi", "kolkata"} else 0.4
    activity_index = 0.8

    risk_input = RiskInput(
        city=city,
        pincode=pincode,
        avg_daily_income=avg_daily_income,
        platform=platform,
        external_frequency_index=external_frequency_index,
        activity_index=activity_index,
    )

    risk = calculate_risk(risk_input)
    risk.worker_id = worker_id
    RISKS.append(risk)

    policy = Policy(
        policy_id=str(uuid4()),
        worker_id=worker_id,
        weekly_premium=risk.suggested_weekly_premium,
        coverage_per_week=round(avg_daily_income * 7 * 0.8, 2),
        created_at=datetime.utcnow(),
    )
    POLICIES.append(policy)

    metrics = build_metrics(RISKS, POLICIES, CLAIMS, EVENTS)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "policies": POLICIES,
            "claims": CLAIMS[-10:],
            "metrics": metrics,
            "message": f"Onboarded {name} with risk band {risk.risk_band.upper()} and weekly premium ₹{risk.suggested_weekly_premium}",
            "current_worker": WORKERS[worker_id],
            "current_risk": risk,
            "current_policy": policy,
        },
    )


@app.post("/trigger", response_class=HTMLResponse)
async def trigger_event(
    request: Request,
    worker_id: str = Form(...),
    disruption_type: str = Form(...),
    severity: int = Form(...),
    description: str = Form(...),
):
    worker = WORKERS.get(worker_id)
    if not worker:
        metrics = build_metrics(RISKS, POLICIES, CLAIMS, EVENTS)
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "policies": POLICIES,
                "claims": CLAIMS[-10:],
                "metrics": metrics,
                "error": f"Unknown worker {worker_id}. Onboard first.",
            },
        )

    event = DisruptionEvent(
        event_id=str(uuid4()),
        worker_id=worker_id,
        disruption_type=DisruptionType(disruption_type),
        severity=severity,
        description=description,
        start_time=datetime.utcnow(),
    )
    EVENTS.append(event)

    avg_daily_income = worker["avg_daily_income"]

    disruption_input = DisruptionInput(
        disruption_type=disruption_type,
        severity=severity,
        rainfall_mm=severity * 15.0,
        heat_index=35 + severity * 2,
        aqi=120 + severity * 40,
        flood_alert=severity >= 4,
        curfew=severity >= 4,
    )

    triggered, model_payout = evaluate_triggers(disruption_input, avg_daily_income)

    message = "No payout triggered; event below threshold."
    fraud_signals = []
    if triggered:
        policy = next((p for p in POLICIES if p.worker_id == worker_id), None)
        if policy:
            claim = Claim(
                claim_id=str(uuid4()),
                worker_id=worker_id,
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

    metrics = build_metrics(RISKS, POLICIES, CLAIMS, EVENTS)
    current_worker = WORKERS.get(worker_id)
    current_risk = next((r for r in RISKS if r.worker_id == worker_id), None)
    current_policy = next((p for p in POLICIES if p.worker_id == worker_id), None)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "policies": POLICIES,
            "claims": CLAIMS[-10:],
            "metrics": metrics,
            "message": message,
            "fraud_signals": fraud_signals,
            "current_worker": current_worker,
            "current_risk": current_risk,
            "current_policy": current_policy,
        },
    )


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    metrics = build_metrics(RISKS, POLICIES, CLAIMS, EVENTS)
    return templates.TemplateResponse(
        "analytics.html", {"request": request, "metrics": metrics}
    )


@app.get("/analytics/metrics", response_model=AnalyticsMetrics)
async def analytics_metrics():
    return build_metrics(RISKS, POLICIES, CLAIMS, EVENTS)
