# 🛡️ GigShield — AI-Powered Parametric Income Insurance
### Guidewire DEVTrails 2026 | Phase 2 Submission
> **Team Trailblazers** · Food Delivery Persona — Zomato / Swiggy

---

## 🚨 The Problem

India's 15 million gig delivery workers lose **20–30% of monthly income** to disruptions they cannot control. When rain hits, when pollution spikes, when a curfew drops — orders stop. Income stops. Nothing compensates them.

**Rajesh Kumar, a Swiggy rider in Mumbai, earns ₹500/day. During monsoon season, heavy rainfall blocks deliveries for hours at a time. He has zero income protection. No claim process exists for him.**

Traditional insurance fails gig workers because:
- Monthly premiums don't match a week-to-week earning cycle
- Manual claims take days — gig workers need money the same day
- Processes are too complex for daily-wage workers

---

## 💡 Our Solution

GigShield is a **parametric income insurance platform** — payouts are triggered by objective external data, not worker-filed claims.

- Worker pays **₹49–₹99/week**
- System monitors live weather + AQI APIs **every 30 minutes**
- Threshold crossed → AI validates → **UPI payout sent instantly**
- **No forms. No phone calls. No waiting.**

**Coverage:** Income loss only. Excludes health, vehicle, accidents, war, pandemics, and terrorism.

---

## ✅ Phase 2 — What We Built & Demonstrated

Every feature below is **live and demonstrated** in our Phase 2 demo video:

| Feature | Status | Demonstrated |
|---|---|---|
| FastAPI backend running | ✅ | Server boot shown |
| Random Forest ML model loaded | ✅ | Risk score 64/100 shown live |
| Background monitor (30 min polling) | ✅ | Active on startup |
| Worker onboarding → risk scoring | ✅ | Rajesh Kumar demo |
| Dynamic premium calculation | ✅ | ₹99/week shown with breakdown |
| Parametric trigger detection | ✅ | 50mm rainfall threshold crossed |
| Auto-claim generation | ✅ | No worker action needed |
| 6-layer fraud detection | ✅ | All layers passed, score: 0 |
| Instant payout simulation | ✅ | ₹1,050 credited to UPI |

---

## 🧠 AI / ML Architecture

### Model 1 — Random Forest Risk Engine

Trained on **50,000 synthetic samples** across **12 real-time risk features:**

| Feature | Description | Source |
|---|---|---|
| `historical_rain_risk` | City-level rainfall frequency | IMD historical data |
| `historical_heat_risk` | Heat event frequency | IMD records |
| `historical_flood_risk` | Derived from rain + city topology | NDMA flood zones |
| `weather_forecast_risk` | 7-day ahead forecast score | OpenWeatherMap |
| `season_factor` | Monsoon 0.8 / Summer 0.6 / Winter 0.3 | IMD seasonal classification |
| `location_density` | Urban density multiplier | Census city data |
| `platform_volatility` | Platform disruption exposure | Delivery platform patterns |
| `worker_experience_days` | Normalised experience (loyalty) | Worker onboarding data |
| `worker_avg_daily_income` | Normalised income bracket | Worker declared income |
| `historical_claim_rate` | Past claim frequency | Internal claims DB |
| `current_aqi` | Live AQI normalised 0–1 | AQICN API |
| `is_festival_season` | Oct–Dec and Mar–Apr flag | Cultural calendar |

**Model configuration:**
- Algorithm: Random Forest Regressor (scikit-learn)
- Estimators: 100 trees · Max depth: 12
- Split: 80% train / 20% test · R² evaluated on test set
- Auto-trains on startup if no saved model found
- Persisted to `models/gigshield_risk_model.pkl` after training

**Live demo result — Rajesh Kumar, Mumbai:**
- Risk score: **64 / 100**
- Risk band: **High**
- Reasoning: Mumbai rain risk 85/100 + flood risk 90/100 + active monsoon season (factor 0.8)

**City risk mapping (IMD + NDMA aligned):**

| City | Rain Risk | Heat Risk | Flood Risk |
|---|---|---|---|
| Mumbai | 85 | 40 | 90 |
| Kolkata | 80 | 65 | 85 |
| Chennai | 75 | 70 | 80 |
| Delhi | 30 | 85 | 20 |
| Bangalore | 50 | 35 | 30 |
| Hyderabad | 45 | 70 | 35 |

---

### Model 2 — Dynamic Premium Calculator

**Formula:** `Base + Risk Loading + Location Adjustment + Experience Adjustment + Forecast Adjustment`

| Component | Logic | Range |
|---|---|---|
| Base Premium | 2% of weekly income | Anchored to earnings |
| Risk Loading | 0–3% of income scaled to risk score | Higher score = higher loading |
| Location Adjustment | ±10% for coastal/flood-prone cities | Mumbai/Chennai = +10% |
| Experience Adjustment | −8% loyalty (6+ months) / +5% new worker | Rewards loyalty |
| Forecast Adjustment | ±15% based on 7-day forecast | Dynamic weekly update |

**Output:** Clamped ₹49–₹99/week · Coverage = 80% of weekly income

**Live demo result — Rajesh Kumar:**
- Risk score 64 → High band → premium ₹99/week
- Weekly coverage: **₹2,800**

---

### Model 3 — 6-Layer Fraud Detection Engine

Every auto-claim passes through all 6 layers before payout is released:

| Layer | Check | Flag Condition |
|---|---|---|
| 1. Location spoofing | GPS vs disruption zone | Worker > 5km outside affected area |
| 2. Collusion detection | Cluster of accounts, same network | Multiple accounts filing simultaneously |
| 3. Duplicate prevention | Same worker, same trigger, same day | Already paid today |
| 4. Earnings consistency | Declared vs estimated income | > 40% deviation |
| 5. Velocity check | Claims vs historical average | 3× above monthly norm |
| 6. Temporal anomaly | Claim timing vs disruption window | Filed outside event timeframe |

**Live demo result — Rajesh Kumar claim:**
- Fraud score: **0**
- Confidence: **85%**
- All 6 layers: **PASSED**
- Action: **APPROVED**

**Phase 3:** Isolation Forest anomaly detection replaces rule-based scoring with ML-probability fraud model.

---

## ⚡ Parametric Trigger System

Thresholds defined from authoritative government and health sources:

| # | Trigger | Threshold | Justification | Payout |
|---|---|---|---|---|
| 1 | Heavy Rain | > 50mm/day | IMD defines heavy rain as > 64.4mm — 50mm is early warning | 70% daily earning |
| 2 | Extreme Heat | > 45°C / 3hrs | WHO outdoor worker heat stress threshold | 50% daily earning |
| 3 | Severe Pollution | AQI > 300 / 4hrs | CPCB Severe category — outdoor work advisory | 60% daily earning |
| 4 | Flood Alert | NDMA bulletin | National Disaster Management Authority alert | 100% daily earning |
| 5 | Social Disruption | Admin-verified | Cross-verified with news API + admin audit trail | 80% daily earning |

**Live demo result:**
- Trigger: Heavy Rain
- Rainfall detected: **58mm** (threshold: 50mm) ✅
- Auto-claim: **generated**
- Payout: **₹1,050 credited to UPI**

> One trigger per worker per day. Combined disruptions → highest applicable payout.

---

## 🔒 Adversarial Defense & Anti-Spoofing Strategy

Parametric insurance is uniquely vulnerable — payouts fire on data, not human review. GigShield is hardened at every layer.

**GPS Spoofing Defense**
Location jumps > 10km in under 5 minutes flagged as teleportation. Declared pincode cross-validated against real-time location at claim time.

**Fake Weather Claim Prevention**
Workers cannot self-report disruptions. Every trigger is driven exclusively by OpenWeatherMap + AQICN data. Claims only initiate when API threshold is crossed and worker's registered city matches affected zone.

**Coordinated Fraud Detection**
Multiple accounts from same device, network, or registration cluster filing simultaneously are quarantined. Velocity checks flag 3× above monthly average.

**Identity Verification**
Workers tied to delivery platform partner ID. UPI handle validated against registered name. Device fingerprinting prevents multi-account abuse.

**Duplicate & Replay Prevention**
Every claim assigned unique hash: worker ID + trigger type + city + timestamp. Duplicate submissions rejected at DB level regardless of session.

**Admin Event Security**
Social disruption triggers require verified admin with 2FA. Full audit trail on every action. No worker-facing interface can create or modify triggers.

> **Design principle:** Every layer protects honest workers from abuse while ensuring legitimate claims are never wrongly blocked.

---

## ⚠️ Coverage Exclusions

Per standard insurance domain requirements, GigShield does **NOT** pay out for:
- War, armed conflict, or military operations
- Government-declared pandemics or public health emergencies
- Terrorism or acts of political violence
- Nuclear, chemical, or biological incidents
- Worker voluntary platform deactivation or ban
- Pre-existing zone restrictions active at policy purchase
- Income loss from worker negligence or misconduct

Workers acknowledge all exclusions via mandatory policy acceptance at onboarding.

---

## ⚙️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend (Phase 1) | HTML, CSS, JavaScript | Core flow validated fast |
| Frontend (Phase 2+) | Next.js + Tailwind CSS | PWA — no install, WhatsApp shareable |
| Backend | Python FastAPI | Same language as ML, auto-generates API docs |
| Database | PostgreSQL + Supabase | Free hosted, built-in auth, 4 core tables |
| ML / AI | scikit-learn Random Forest | 50k samples, no GPU, runs on any machine |
| Weather | OpenWeatherMap API | Free tier, real rainfall + temperature |
| AQI | AQICN API | Free tier, real AQI by city |
| Payments | Razorpay Sandbox | UPI simulation — Phase 3 |

---

## 🗺️ System Workflow

```
Worker registers → name, city, platform, UPI, daily income
        ↓
ML Risk Engine: 12 features → risk score → risk band
        ↓
Premium Calculator: personalised weekly rate with full breakdown
        ↓
Worker pays via UPI → policy active Mon–Sun
        ↓
Background monitor polls OpenWeatherMap + AQICN every 30 mins
        ↓
Threshold crossed → disruption event logged
        ↓
Auto-claim created → 6-layer fraud validation runs
        ↓
All layers pass → payout initiated to UPI instantly
        ↓
Worker notified · dashboard updated · admin log written
```

---

## 📁 Repository Structure

```
GigShield/
├── app/
│   ├── main.py                   # FastAPI app, startup ML training
│   ├── db.py                     # Supabase connection
│   ├── schemas.py                # Pydantic models
│   └── services/
│       ├── ml_risk.py            # Random Forest (50k samples, 12 features)
│       ├── premium_calculator.py # Dynamic premium engine
│       ├── triggers.py           # OpenWeatherMap + AQICN polling
│       ├── fraud.py              # 6-layer fraud detection
│       ├── risk.py               # Risk aggregation
│       └── integrations.py       # External API wrappers
│
├── frontend/
│   ├── src/app/
│   │   ├── auth/                 # Login / registration
│   │   ├── dashboard/            # Worker dashboard
│   │   ├── plans/                # Coverage tier selection
│   │   └── page.js               # Landing page
│   └── components/
│
├── models/
│   ├── gigshield_risk_model.pkl  # Trained Random Forest
│   └── gigshield_scaler.pkl      # Feature scaler
│
├── schema.sql
├── requirements.txt
└── test_db.py
```

---

## 🗄️ Database Schema

| Table | Purpose |
|---|---|
| `workers` | Profile, city, platform, UPI handle, earnings tier |
| `policies` | Active weekly coverage, premium, coverage amount, status |
| `claims` | Trigger type, payout amount, fraud score, validation status |
| `disruption_events` | API-detected events by city, value, source, timestamp |

---

## 🚀 Setup

**Backend**
```bash
git clone https://github.com/Ghoulayush/GuideWire.git
cd GuideWire
pip install -r requirements.txt
uvicorn app.main:app --reload
```

ML model trains automatically on first startup. Loads from `models/` on subsequent runs.

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/workers/onboard` | Register worker, ML risk score, create policy |
| POST | `/events/trigger` | Fire disruption event manually |
| POST | `/api/simulate/rain` | Simulate full rain trigger end-to-end |
| GET | `/dashboard` | Active policies, claims, payout summary |
| GET | `/analytics/metrics` | Full metrics breakdown |
| GET | `/fraud/stats` | Fraud detection layer summary |
| GET | `/health` | Service health check |
| GET | `/test/ml` | Verify ML model loaded and predicting |

---

## 🧪 Live Demo Results

**Worker onboarded:** Rajesh Kumar · Swiggy · Mumbai · ₹500/day
**Risk score:** 64/100 · High band
**Weekly premium:** ₹99 · Coverage: ₹2,800

**Trigger fired:** Heavy rain 58mm (threshold 50mm exceeded)
**Claim:** Auto-generated · No worker action
**Fraud score:** 0 · All 6 layers passed · Confidence 85%
**Payout:** ₹1,050 credited to UPI instantly

**System metrics:** 1 worker · 1 policy · 1 claim · ₹1,050 total payout

---

## 🗓️ Phase Roadmap

### Phase 1 ✅ — Ideation & Foundation
Persona research · premium formula · 5 triggers defined · HTML/CSS/JS prototype · README

### Phase 2 ✅ — Automation & Protection (Current)
FastAPI backend · Supabase DB · Random Forest ML (50k samples) · dynamic premium · live API triggers · auto-claim pipeline · 6-layer fraud detection · Next.js frontend

### Phase 3 — Scale & Optimise
Isolation Forest fraud model · Razorpay UPI payout · APScheduler automation · worker forecast dashboard · admin analytics dashboard · final demo video + pitch deck

---

## 👥 Team Trailblazers

| Role | Responsibility |
|---|---|
| Team Lead / Frontend | Next.js UI, onboarding, dashboard |
| Backend Engineer | FastAPI, Supabase, trigger pipeline |
| ML Engineer | Random Forest, premium calculator, fraud engine |
| Docs & Video | README, demo video, pitch deck |

---

*GigShield — protecting gig workers when the city shuts down.*
*Guidewire DEVTrails 2026 |  Team Trailblazers*
