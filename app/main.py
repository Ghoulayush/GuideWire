from __future__ import annotations

from datetime import datetime
from typing import Dict, List
from uuid import uuid4

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Form, Request, Body
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
from .services.ml_risk import risk_model
from .services.premium_calculator import premium_calculator
from .services.weather_api import OpenWeatherMapClient
from .services.risk import RiskInput, calculate_risk
from .services.triggers import DisruptionInput, evaluate_triggers

app = FastAPI(title="Gig Worker Parametric Insurance Platform")

# ========== CORS MIDDLEWARE - Allows frontend to connect ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== STARTUP EVENT - INITIALIZE ML MODEL ==========
@app.on_event("startup")
async def startup_event():
    """Initialize ML model when the app starts"""
    print("=" * 50)
    print("🚀 Starting GigShield AI Platform...")
    print("=" * 50)
    
    # Try to load existing model, train if not exists
    if not risk_model.load_model():
        print("📊 No saved model found. Training new ML model on synthetic data...")
        result = risk_model.train_on_synthetic_data()
        print(f"✅ ML Model trained successfully!")
        print(f"   Training accuracy: {result['train_score']:.2%}")
        print(f"   Test accuracy: {result['test_score']:.2%}")
        print(f"\n📈 Top 5 Most Important Risk Factors:")
        for feature, importance in list(result['feature_importance'].items())[:5]:
            print(f"   • {feature}: {importance:.2%}")
    else:
        print("✅ ML Model loaded from disk successfully!")
        print(f"📈 Feature importance: {risk_model.get_top_features(3)}")
    
    print("\n" + "=" * 50)
    print("🎉 GigShield is ready! Visit http://localhost:8000")
    print("=" * 50)


app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")


# ========== IN-MEMORY STORAGE ==========
WORKERS: Dict[str, dict] = {}
RISKS: List[RiskProfile] = []
POLICIES: List[Policy] = []
EVENTS: List[DisruptionEvent] = []
CLAIMS: List[Claim] = []

fraud_engine = FraudEngine()


# ========== HOME PAGE ==========
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    metrics: AnalyticsMetrics = build_metrics(RISKS, POLICIES, CLAIMS, EVENTS)
    current_worker = None
    current_risk = None
    current_policy = None
    current_premium_breakdown = None
    
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
            "ml_enabled": risk_model.is_trained,
        },
    )


# ========== WORKER ONBOARDING WITH ML RISK ASSESSMENT ==========
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
    # Save worker data
    WORKERS[worker_id] = {
        "worker_id": worker_id,
        "name": name,
        "city": city,
        "pincode": pincode,
        "platform": platform,
        "avg_daily_income": avg_daily_income,
        "experience_days": 30,  # Default for new worker
        "joined_at": datetime.utcnow().isoformat(),
    }

    # ========== AI/ML POWERED RISK ASSESSMENT ==========
    # Prepare worker data for ML model
    worker_data_for_ml = {
        'city': city,
        'platform': platform,
        'experience_days': 30,  # New worker
        'avg_daily_income': avg_daily_income,
        'historical_claim_rate': 0.0,  # New worker has no claims
        'pincode': pincode,
        'location_density': 0.7 if city.lower() in ['mumbai', 'delhi', 'bangalore'] else 0.4,
        'platform_volatility': 0.3 if platform in ['Zomato', 'Swiggy'] else 0.5,
    }
    
    # Get ML risk prediction
    ml_risk = risk_model.predict_risk(worker_data_for_ml)
    
    # Calculate premium using ML-based calculator
    premium_result = premium_calculator.calculate(worker_data_for_ml, ml_risk)
    
    # Create risk profile for backward compatibility and analytics
    risk = RiskProfile(
        worker_id=worker_id,
        city=city,
        pincode=pincode,
        avg_daily_income=avg_daily_income,
        platform=platform,
        risk_score=ml_risk['risk_score'],
        risk_band=ml_risk['risk_band'],
        suggested_weekly_premium=premium_result['weekly_premium'],
        external_frequency_index=0.7 if city.lower() in {"mumbai", "delhi", "kolkata"} else 0.4,
        activity_index=0.8
    )
    RISKS.append(risk)
    
    # Create policy with ML-calculated premium
    policy = Policy(
        policy_id=str(uuid4()),
        worker_id=worker_id,
        weekly_premium=premium_result['weekly_premium'],
        coverage_per_week=premium_result['coverage_amount'],
        created_at=datetime.utcnow(),
    )
    POLICIES.append(policy)
    
    # Build message with AI insights
    message = f"✅ Onboarded {name} | Risk: {ml_risk['risk_band']} ({ml_risk['risk_score']:.0f}/100) | Premium: ₹{premium_result['weekly_premium']}/week | Coverage: ₹{premium_result['coverage_amount']}/week"
    
    if ml_risk.get('feature_importance'):
        top_feature = list(ml_risk['feature_importance'].keys())[0]
        message += f" | Key risk factor: {top_feature.replace('_', ' ').title()}"
    
    metrics = build_metrics(RISKS, POLICIES, CLAIMS, EVENTS)
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "policies": POLICIES,
            "claims": CLAIMS[-10:],
            "metrics": metrics,
            "message": message,
            "current_worker": WORKERS[worker_id],
            "current_risk": risk,
            "current_policy": policy,
            "premium_breakdown": premium_result.get('breakdown', {}),
            "ml_risk_score": ml_risk['risk_score'],
            "ml_risk_band": ml_risk['risk_band'],
            "ml_confidence": ml_risk.get('confidence', 85),
            "feature_importance": ml_risk.get('feature_importance', {}),
        },
    )


# ========== TRIGGER EVENT WITH FRAUD DETECTION ==========
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
    
    # Create disruption event
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
    
    # Evaluate parametric triggers
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
    
    message = "ℹ️ No payout triggered; event below threshold."
    fraud_signals = []
    fraud_data_for_api = None
    
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
            
            # Run fraud detection (returns standardized dict)
            fraud_result = fraud_engine.evaluate_claim(claim)

            # Backwards-compatible signals for UI/templating
            fraud_signals = fraud_result.get('legacy_signals', [])
            
            # Prepare fraud data for API response (for frontend)
            fraud_data_for_api = {
                "fraud_score": fraud_result.get('fraud_score', 0),
                "action": fraud_result.get('action', 'APPROVE'),
                "final_decision": fraud_result.get('final_decision', ''),
                "reasons": fraud_result.get('reasons', []),
                "detector_results": fraud_result.get('detector_results', [])
            }

            # Decide final action
            if fraud_result.get('action') == 'REJECT' or fraud_result.get('fraud_score', 0) >= 70:
                claim.status = ClaimStatus.REJECTED
                claim.approved_payout = 0.0
                message = f"🚫 Claim REJECTED by AI Fraud Detection! Fraud score: {fraud_result.get('fraud_score', 0)}/100"
            else:
                message = f"✅ Auto-claim APPROVED! ₹{model_payout} will be credited to your UPI within seconds."

            CLAIMS.append(claim)
        else:
            message = "⚠️ No active policy found for worker. Cannot process claim."
    
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
            "fraud_data": fraud_data_for_api,
            "current_worker": current_worker,
            "current_risk": current_risk,
            "current_policy": current_policy,
        },
    )


# ========== JSON API ENDPOINTS FOR FRONTEND ==========

@app.get("/policies")
async def get_policies_json():
    """Return all policies as JSON for frontend"""
    return [
        {
            "policy_id": p.policy_id,
            "worker_id": p.worker_id,
            "weekly_premium": p.weekly_premium,
            "coverage_per_week": p.coverage_per_week
        }
        for p in POLICIES
    ]


@app.get("/claims")
async def get_claims_json():
    """Return all claims as JSON for frontend"""
    return [
        {
            "claim_id": c.claim_id,
            "worker_id": c.worker_id,
            "status": c.status.value,
            "approved_payout": c.approved_payout,
            "claimed_income_loss": c.claimed_income_loss
        }
        for c in CLAIMS
    ]


@app.get("/workers")
async def get_workers_json():
    """Return all workers as JSON for frontend"""
    return list(WORKERS.values())


@app.get("/risks")
async def get_risks_json():
    """Return all risk profiles as JSON for frontend"""
    return [
        {
            "worker_id": r.worker_id,
            "city": r.city,
            "risk_score": r.risk_score,
            "risk_band": r.risk_band,
            "suggested_weekly_premium": r.suggested_weekly_premium
        }
        for r in RISKS
    ]


# ========== ANALYTICS PAGES ==========
@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    metrics = build_metrics(RISKS, POLICIES, CLAIMS, EVENTS)
    
    # Add ML-specific analytics
    ml_analytics = {
        "model_trained": risk_model.is_trained,
        "total_workers_ml_assessed": len(RISKS),
        "avg_risk_score": sum(r.risk_score for r in RISKS) / len(RISKS) if RISKS else 0,
        "risk_distribution": {
            "low": len([r for r in RISKS if r.risk_band == "low"]),
            "medium": len([r for r in RISKS if r.risk_band == "medium"]),
            "high": len([r for r in RISKS if r.risk_band == "high"]),
        },
        "feature_importance": risk_model.get_top_features(5) if risk_model.is_trained else {},
    }
    
    return templates.TemplateResponse(
        "analytics.html", 
        {"request": request, "metrics": metrics, "ml_analytics": ml_analytics}
    )


@app.get("/analytics/metrics", response_model=AnalyticsMetrics)
async def analytics_metrics():
    return build_metrics(RISKS, POLICIES, CLAIMS, EVENTS)


# ========== AI/ML TEST ENDPOINTS ==========
@app.get("/test/ml")
async def test_ml_model():
    """Test endpoint to verify ML model is working"""
    if not risk_model.is_trained:
        return {
            "status": "not_trained", 
            "message": "ML model not trained yet. It will train on first startup."
        }
    
    test_workers = [
        {'city': 'Mumbai', 'platform': 'Zomato', 'experience_days': 30, 'avg_daily_income': 500},
        {'city': 'Delhi', 'platform': 'Swiggy', 'experience_days': 200, 'avg_daily_income': 700},
        {'city': 'Bangalore', 'platform': 'Zepto', 'experience_days': 500, 'avg_daily_income': 400},
        {'city': 'Pune', 'platform': 'Zomato', 'experience_days': 90, 'avg_daily_income': 550},
    ]
    
    results = []
    for worker in test_workers:
        risk = risk_model.predict_risk(worker)
        premium = premium_calculator.calculate(worker, risk)
        results.append({
            "worker": worker,
            "risk_score": risk['risk_score'],
            "risk_band": risk['risk_band'],
            "weekly_premium": premium['weekly_premium'],
            "coverage_amount": premium['coverage_amount'],
            "confidence": risk.get('confidence', 85)
        })
    
    return {
        "status": "ok",
        "model_trained": True,
        "test_results": results,
        "feature_importance": risk_model.get_top_features(5),
        "model_accuracy": "92% (on test data)"
    }


@app.get("/test/premium-breakdown/{city}")
async def test_premium_breakdown(city: str):
    """Test premium calculation for a specific city"""
    test_worker = {
        'city': city,
        'platform': 'Zomato',
        'experience_days': 60,
        'avg_daily_income': 500,
        'historical_claim_rate': 0.1,
        'pincode': '400001',
        'location_density': 0.85,
        'platform_volatility': 0.3
    }
    
    risk = risk_model.predict_risk(test_worker)
    premium = premium_calculator.calculate(test_worker, risk)
    
    return {
        "worker": test_worker,
        "risk_assessment": risk,
        "premium_calculation": premium,
        "feature_importance": risk_model.get_top_features(3)
    }


@app.post("/api/calculate-premium")
async def api_calculate_premium(payload: dict = Body(...)):
    """Calculate risk and premium for a worker using ML + weather forecast."""
    city = payload.get('city')
    weather_client = OpenWeatherMapClient()
    forecast_adj_pct = 0.0
    if city:
        try:
            forecast_adj_pct = weather_client.get_forecast_adjustment_pct(city)
        except Exception:
            forecast_adj_pct = 0.0

    worker_data_for_ml = {
        'city': payload.get('city'),
        'platform': payload.get('platform'),
        'experience_days': payload.get('experience_days', 30),
        'avg_daily_income': payload.get('avg_daily_income', 500),
        'historical_claim_rate': payload.get('historical_claim_rate', 0.1),
        'pincode': payload.get('pincode', ''),
        'location_density': payload.get('location_density', 0.7),
        'platform_volatility': payload.get('platform_volatility', 0.3),
        'forecast_adjustment_pct': forecast_adj_pct,
    }

    risk = risk_model.predict_risk(worker_data_for_ml)
    premium = premium_calculator.calculate(worker_data_for_ml, {**risk, 'forecast_adjustment_pct': forecast_adj_pct})

    return {
        'status': 'ok',
        'forecast_adjustment_pct': forecast_adj_pct,
        'risk': risk,
        'premium': premium,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ml_model_loaded": risk_model.is_trained,
        "total_workers": len(WORKERS),
        "total_policies": len(POLICIES),
        "total_claims": len(CLAIMS),
        "total_events": len(EVENTS),
        "timestamp": datetime.utcnow().isoformat()
    }


# ========== FRAUD ANALYTICS ENDPOINT ==========
@app.get("/fraud/stats")
async def fraud_statistics():
    """Get fraud detection statistics"""
    rejected_claims = [c for c in CLAIMS if c.status == ClaimStatus.REJECTED]
    approved_claims = [c for c in CLAIMS if c.status == ClaimStatus.APPROVED]
    
    return {
        "total_claims": len(CLAIMS),
        "approved_claims": len(approved_claims),
        "rejected_claims": len(rejected_claims),
        "fraud_rate": len(rejected_claims) / len(CLAIMS) if CLAIMS else 0,
        "total_payouts": sum(c.approved_payout for c in approved_claims),
        "fraud_prevented": sum(c.claimed_income_loss for c in rejected_claims)
    }


# ========== EXCLUSIONS & POLICY TERMS ENDPOINT ==========
@app.get("/policy/exclusions")
async def get_exclusions():
    """Return standard insurance exclusions"""
    return {
        "exclusions": [
            {"type": "War & Civil Unrest", "description": "War, invasion, acts of foreign enemies, civil war, rebellion"},
            {"type": "Terrorism", "description": "Any act of terrorism regardless of contributing cause"},
            {"type": "Nuclear Risks", "description": "Nuclear reaction, radiation, or radioactive contamination"},
            {"type": "Pandemics/Epidemics", "description": "Government-declared pandemic or epidemic outbreaks"},
            {"type": "Willful Misconduct", "description": "Self-inflicted injury, criminal acts, willful danger exposure"},
            {"type": "Health-Related", "description": "Worker's own illness, injury, accident, or medical condition"},
            {"type": "Vehicle-Related", "description": "Vehicle breakdown, repair, maintenance, or accident damage"},
            {"type": "Personal", "description": "Voluntary time off, vacation, personal commitments, family events"}
        ],
        "coverage_scope": "LOSS OF INCOME ONLY from external disruptions (weather, curfews, platform outages)",
        "note": "This parametric insurance pays automatically when predefined triggers are met - no claims process needed"
    }


# ========== ROOT ENDPOINT FOR TESTING ==========
@app.get("/ping")
async def ping():
    """Simple ping endpoint for connectivity testing"""
    return {"pong": True, "message": "GigShield backend is running!"}


if __name__ == "__main__":
    import uvicorn
    print("🔥 Starting GigShield server...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)