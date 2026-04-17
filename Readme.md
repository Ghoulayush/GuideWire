# GigShield - AI-Powered Parametric Income Insurance
### Guidewire DEVTrails 2026 | Phase 3 Submission
Team Trailblazers | Food Delivery Persona (Zomato / Swiggy)

---

## Problem

Gig delivery workers lose income when city disruptions happen (heavy rain, flood alerts, pollution spikes, curfew/social disruption). Traditional claims-based insurance is too slow and too complex for daily-wage workflows.

---
## Demo

- YouTube (project working): https://youtu.be/3Ctuljb2Hz0?si=ovQXZQUNiSNspLaC
- Google Drive (demo folder): https://drive.google.com/drive/folders/1uZdU1CIAauEIvR4QcFW1hgWTwGMJb9Fs?usp=drive_link

---
## What GigShield Does

GigShield uses a parametric model:

- Worker onboarding -> AI risk scoring -> dynamic weekly premium.
- External disruption signals + trigger rules evaluate payout eligibility.
- Claim decisions go through multi-layer fraud detection.
- Approved claims can be pushed through instant payout simulation and UPI flow.

Core principle: no manual worker paperwork for trigger-based claims.

---

## Phase 3 - Latest Work Completed

This repository now includes the Phase 3 scope in code and demo flow:

1. Model hardening and diagnostics
- Canonical risk model path with metadata (`model_version`, `feature_schema_version`, `trained_at`, `training_mode`).
- Input sanitization, clipping, fallback handling, and guardrail-based recommendations.
- Runtime diagnostics exposed via health endpoint (`model_runtime_diagnostics`).

2. Scenario-driven robustness
- Synthetic stress scenarios for rain/flood, heatwave + AQI, low-signal payloads, and adversarial extremes.
- Bounded output (`0-100`) with confidence bands and reason codes.

3. Fraud engine integration in runtime flow
- `/events/trigger` builds claim evidence (GPS trail, weather mismatch checks, area burst checks, historical pattern).
- Weighted fraud decisioning with advanced detector integration.
- Decision bands used in frontend: approve (<40), review (40-69), reject (>=70).

4. Subscription and payment integration
- Razorpay order + verify endpoints.
- Live mode when keys are configured, mock mode fallback when keys are missing.
- Subscription status and admin subscription listing endpoints.

5. Admin and insurer operations interfaces
- Admin console for workers, policies, claims, subscriptions.
- Insurer dashboard for loss ratio, reserves, and high-risk zone planning.

---

## Current Deployment Status

- Frontend: deployed
- Backend: deployed

Use your live base URLs:

- Frontend URL: `<YOUR_FRONTEND_URL>`
- Backend URL: `<YOUR_BACKEND_URL>`

Set frontend API routing using `NEXT_PUBLIC_API_URL=<YOUR_BACKEND_URL>` in your frontend deployment environment.

---

## Demo Walkthrough (How the live demo works)

1. Worker authentication
- Open `<FRONTEND_URL>/auth`.
- Sign up or log in with Supabase auth.

2. Worker onboarding and policy creation
- Go to Dashboard and submit worker details.
- Backend computes risk + premium and creates policy.

3. Event simulation and claim decision
- Trigger disruption event from dashboard.
- Backend runs trigger logic + fraud engine.
- Response includes claim timeline, fraud score, and decision message.

4. Subscription checkout
- Go to `<FRONTEND_URL>/subscription`.
- Choose weekly plan (Essential/Growth/Shield Max).
- Razorpay flow runs in live mode if keys exist; mock mode otherwise.

5. Payout flow
- From claims table, start payout.
- Track payout status and UPI QR details.

6. Admin/insurer access
- Admin login: `<FRONTEND_URL>/admin/login`
- Admin dashboard: `<FRONTEND_URL>/admin`
- Insurer metrics dashboard: `<FRONTEND_URL>/admin/insurer`

Current admin credentials (demo only):
- Email: `admin@gigshield.local`
- Password: `admin123`

---

## System Architecture

### Backend (FastAPI)
- Worker onboarding, risk scoring, premium generation.
- Trigger evaluation and automated claim decisioning.
- Fraud analysis and insurer analytics.
- Razorpay order/verification + subscription records.

### Frontend (Next.js)
- Supabase login/sign-up for worker flow.
- Dashboard for onboarding, trigger simulation, claim and payout view.
- Subscription checkout page with Razorpay integration.
- Admin operations + insurer metrics views.

### Data Layer
- Supabase/Postgres persistence for workers, policies, claims, events, subscriptions.
- In-memory fallback path also exists for non-persistent runtime.

---

## Key API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/workers/onboard` | Register worker, score risk, issue policy |
| POST | `/events/trigger` | Trigger disruption and process claim/fraud decision |
| GET | `/dashboard` | Dashboard aggregate data |
| GET | `/analytics/metrics` | Platform metrics |
| GET | `/insurer/metrics` | Loss ratio and reserve metrics |
| GET | `/fraud/stats` | Fraud outcome statistics |
| GET | `/health` | Health + model diagnostics |
| GET | `/test/ml` | ML sanity check endpoint |
| POST | `/payments/razorpay/order` | Create Razorpay order |
| POST | `/payments/razorpay/verify` | Verify payment signature |
| GET | `/payments/subscriptions/{customer_email}` | Customer subscription status |
| GET | `/payments/subscriptions` | Admin subscription listing |
| POST | `/api/payout` | Initiate payout |
| GET | `/api/payout/{transaction_id}` | Track payout status |

---

## Repository Structure

```text
GuideWire/
|- app/
|  |- main.py
|  |- db.py
|  |- repositories/
|  |- services/
|  |  |- ml_risk.py
|  |  |- premium_calculator.py
|  |  |- triggers.py
|  |  |- fraud/
|  |  |- predictive_analytics.py
|  |  |- payout.py
|- frontend/
|  |- src/app/
|  |  |- auth/
|  |  |- home/
|  |  |- dashboard/
|  |  |- simulation/
|  |  |- subscription/
|  |  |- admin/
|  |- src/components/
|  |- src/lib/
|- tests/
|- models/
|- plan.md
|- AGENTS.md
```

---

## Local Setup

### Backend

```bash
git clone https://github.com/Ghoulayush/GuideWire.git
cd GuideWire
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Frontend production commands:

```bash
pnpm build
pnpm start
```

---

## Environment Variables (names only)

Backend:
- `DATABASE_URL`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `USE_DB_PERSISTENCE`
- `AUTO_TRIGGER_MONITORING`
- `EXTERNAL_SIGNALS_MODE`

Frontend:
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_RAZORPAY_KEY_ID`

---

## Validation and Test Coverage

Representative tests included:
- `tests/test_model_hardening.py`
- `tests/test_premium_api.py`
- `tests/test_fraud_ensemble.py`
- `tests/test_fraud_layers_1_3.py`
- `tests/test_fraud_standardization.py`
- `tests/test_tf_detectors.py`

These cover model hardening behavior, API flow checks, and fraud-layer validation paths.

---

## Security Note

Current admin login is demo-oriented and frontend credential based. For production-grade security, replace this with server-side role-based auth (Supabase roles / JWT claims / protected backend admin APIs).

---

## Team

Trailblazers

- Frontend and UX
- Backend and integrations
- AI/ML and fraud modeling
- Documentation and demo

---

GigShield protects delivery workers when disruptions stop earnings.
