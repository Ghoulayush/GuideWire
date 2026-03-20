# 🛡️ GigShield — AI-Powered Parametric Income Insurance for India's Gig Economy

> **Guidewire DEVTrails 2026 | Phase 1 Submission**
> Built for food delivery partners on Zomato & Swiggy

---

## 🚨 The Problem

India has over **15 million gig delivery workers**. They are the backbone of platforms like Zomato and Swiggy — yet they have **zero income protection**.

When extreme weather hits, when AQI crosses dangerous levels, when a sudden curfew shuts down a zone — orders stop. Riders stop earning. And no one compensates them.

**Ravi**, a Swiggy rider in Bengaluru, lost ₹8,000 last monsoon because it rained 14 out of 30 days. He had no insurance. No claim process. No safety net. Just loss.

> These workers lose **20–30% of monthly earnings** to external disruptions they cannot control.

Traditional insurance products don't work here:

- Monthly / annual premiums don't match a week-to-week earning cycle
- Manual claim processes are too complex for daily-wage workers
- Coverage scope (health, vehicle) doesn't address the real problem: **lost income**

---

## 💡 Our Solution: GigShield

**GigShield** is an AI-enabled parametric income insurance platform built exclusively for food delivery workers (Zomato / Swiggy persona).

- Workers pay a **small weekly premium (₹49–₹99/week)**
- When a parametric trigger fires (heavy rain, extreme AQI, curfew) — **no claim form is needed**
- Our system detects the disruption via live APIs, validates it, and **transfers income compensation directly to the worker's UPI wallet** — automatically

**Coverage:** Loss of income only. No health, no vehicle, no accidents — strictly income protection.

---

## 👤 Persona: Food Delivery Partner

**Sub-category chosen:** Food Delivery — Zomato / Swiggy riders

### Who We're Building For

| Attribute       | Details                                            |
| --------------- | -------------------------------------------------- |
| Name            | Ravi Kumar (representative persona)                |
| City            | Bengaluru, Mumbai, Delhi, Hyderabad                |
| Platform        | Zomato / Swiggy                                    |
| Work hours      | 8–12 hours/day, 6–7 days/week                      |
| Weekly earnings | ₹2,500–₹5,000                                      |
| Device          | Android smartphone, moderate data plan             |
| UPI             | Active (PhonePe / GPay)                            |
| Pain point      | No income when weather/disruptions stop deliveries |

### Persona-Based Scenarios

**Scenario 1 — Monsoon in Bengaluru**
Ravi has GigShield coverage this week. On Thursday, rainfall hits 65mm — above our 50mm threshold. The system detects this via OpenWeatherMap API. His GPS confirms he is in an active delivery zone. An automated payout of ₹700 (70% of his ₹1,000 daily earning estimate) is credited to his UPI by evening. He never filed a claim.

**Scenario 2 — Severe AQI in Delhi**
Priya, a Swiggy rider in Delhi, has active coverage. AQI crosses 350 at 10 AM and stays above 300 for 5+ hours. This crosses our pollution trigger threshold. The system auto-initiates a claim, fraud checks pass (she was active that morning), and she receives ₹600 compensation. She sees a notification: _"GigShield has credited ₹600 for pollution disruption on 14 Nov."_

**Scenario 3 — Sudden Zone Curfew in Mumbai**
A local protest shuts down a delivery zone in Andheri. An admin triggers the "social disruption" event for that pincode. All GigShield policyholders in that zone with active coverage receive automatic payouts within 2 hours.

---

## 💰 Weekly Premium Structure & Parametric Triggers

The premium model and trigger system are the two sides of GigShield's core engine. The premium is priced weekly to match how gig workers earn. The triggers are parametric — meaning payouts are driven entirely by objective external data, not worker-filed claims. Together they make the product both affordable and automatic.

### Why Weekly Pricing?

Gig workers earn and spend weekly. A monthly or annual premium creates cash-flow mismatch. Weekly pricing aligns with their earning cycle and reduces the psychological cost of buying insurance.

### Premium Calculation Formula

**Weekly Premium = Base Rate × Zone Risk Multiplier × Earnings Tier Factor**

| Variable                 | Description                                         | Values                                   |
| ------------------------ | --------------------------------------------------- | ---------------------------------------- |
| **Base Rate**            | Minimum weekly coverage cost                        | ₹49                                      |
| **Zone Risk Multiplier** | Historical disruption frequency in worker's pincode | 1.0 (low risk) → 1.8 (high risk)         |
| **Earnings Tier Factor** | Worker's declared weekly income bracket             | 0.9 (₹1,500–2,500) → 1.2 (₹4,000–5,000+) |

**Example Calculation:**

- Ravi, Bengaluru (flood-prone zone, multiplier 1.6), earns ₹3,500/week (factor 1.1)
- Premium = ₹49 × 1.6 × 1.1 = **₹86/week**
- Coverage = 70% of declared weekly earnings, capped at ₹1,500/event

### Coverage Tiers

| Weekly Premium | Max Payout/Event | Coverage Cap |
| -------------- | ---------------- | ------------ |
| ₹49            | ₹500             | ₹1,000/week  |
| ₹69            | ₹850             | ₹1,500/week  |
| ₹99            | ₹1,500           | ₹2,500/week  |

---

### Parametric Triggers

Triggers are objective, data-driven, and automatic. Workers do not need to file claims.

| #   | Trigger Type         | Condition                                         | Data Source                  | Payout             |
| --- | -------------------- | ------------------------------------------------- | ---------------------------- | ------------------ |
| 1   | Heavy Rain           | Rainfall > 50mm/day in worker's city              | OpenWeatherMap API           | 70% daily earning  |
| 2   | Extreme Heat         | Temperature > 45°C for 3+ hours                   | OpenWeatherMap API           | 50% daily earning  |
| 3   | Severe Air Pollution | AQI > 300 for 4+ consecutive hours                | AQICN API                    | 60% daily earning  |
| 4   | Flood / Waterlogging | Flood alert issued for pincode                    | OpenWeatherMap + manual flag | 100% daily earning |
| 5   | Social Disruption    | Curfew / strike in delivery zone (admin-verified) | Admin-triggered event        | 80% daily earning  |

> **Note:** Only one trigger per day can activate. Combined disruptions default to the highest applicable payout.

The trigger thresholds are calibrated to match real disruption patterns in Indian metro cities. Zone risk multipliers in the premium formula are derived from the historical frequency of these same trigger events — so workers in high-disruption zones pay slightly more but are also the most likely to benefit.

---

## 🤖 AI / ML Integration Plan

### 1. Dynamic Premium Calculation (Phase 1 → Phase 2)

**Model:** Random Forest Regressor (scikit-learn)

**Input Features:**

- Worker's city / pincode
- Historical disruption frequency for that zone (past 12 months)
- Season / month (monsoon season = higher risk weight)
- Worker's declared earnings bracket
- Days active per week (from onboarding)

**Output:** Recommended weekly premium in ₹

**Phase 1 approach:** We define the model architecture and feature set. The model is trained on historical weather disruption data + mock earnings data in Phase 2. For Phase 1, premium outputs are validated against our manual formula to confirm the model behaves as expected before going live.

### 2. Fraud Detection AI (Phase 2 → Phase 3)

**Model:** Isolation Forest (anomaly detection) + Rule-Based Validator

**Checks performed on every auto-claim:**

| Check                   | Method                                        | Flag if...                          |
| ----------------------- | --------------------------------------------- | ----------------------------------- |
| GPS location validation | Worker's last known location vs affected zone | >5km outside disruption zone        |
| Activity validation     | Was worker logged active before disruption?   | No activity 2+ hours before trigger |
| Duplicate claim check   | Same worker, same day                         | Already paid today                  |
| Earnings consistency    | Declared earnings vs platform API estimate    | >40% deviation                      |
| Velocity check          | Claims per month vs historical average        | 3× above average                    |

**Phase 1:** Architecture and rules defined. Mock validation function outlined.
**Phase 2:** Isolation Forest trained on synthetic claims data. GPS validation integrated.

---

## 🔒 Adversarial Defense & Anti-Spoofing Strategy

Parametric insurance is uniquely vulnerable to abuse because payouts are triggered by external data rather than verified incidents. GigShield is built with multiple layers of defense to prevent spoofing, manipulation, and fraudulent claims.

### 1. GPS Spoofing Defense

Fake GPS coordinates are the most common attack vector for location-based claims. GigShield counters this by cross-referencing the worker's last 3 known locations to detect teleportation patterns, flagging any location jump exceeding 10km in under 5 minutes, and comparing declared pincode at registration against real-time location at claim time. Any mismatch above a defined threshold is flagged and held for review.

### 2. Fake Weather Claim Prevention

Workers cannot self-report disruptions. Every trigger is driven exclusively by third-party API data from OpenWeatherMap and AQICN — not by worker input. Claims are only initiated when the API threshold is crossed and the worker's registered city matches the affected zone. We cross-validate readings across multiple data points before initiating any claim.

### 3. Collusion & Coordinated Fraud Detection

Our Isolation Forest model detects coordinated fraud patterns where multiple workers from the same device, network, or registration cluster file claims simultaneously in conditions that do not match regional API data. Velocity checks flag any worker whose monthly claim frequency exceeds 3× their historical average.

### 4. Identity & Onboarding Verification

Workers are verified at onboarding using their delivery platform partner ID. UPI handle is validated against the registered name to prevent account substitution. Each worker is tied to a unique device fingerprint — multiple accounts from the same device are automatically flagged.

### 5. Duplicate & Replay Attack Prevention

Every claim event is assigned a unique hash combining worker ID, trigger type, city, and timestamp. Duplicate submissions — even from different sessions — are rejected at the database level. Payouts are strictly limited to one per worker per trigger event per day.

### 6. Admin-Triggered Event Security

Social disruption events such as curfews and strikes can only be triggered by verified admin accounts with two-factor authentication. All admin actions are logged with full audit trails. No worker-facing interface has access to trigger creation or modification.

### 7. Model Adversarial Robustness

The Isolation Forest fraud model is retrained periodically on new claims data to adapt to emerging fraud patterns. Feature drift monitoring tracks whether incoming claim profiles begin deviating significantly from the training distribution — a signal that coordinated gaming may be occurring. Suspicious clusters are quarantined for human review before payouts are released.

> **Design principle:** GigShield's defense strategy assumes adversarial users exist at scale. Every layer is designed to protect honest workers from system abuse while ensuring legitimate claims are never wrongly blocked.

---

## 🛠️ Tech Stack

### Frontend

**Phase 1 Prototype — HTML, CSS, JavaScript**

- Core user flow built to validate onboarding, premium display, plan selection, and dashboard

**Phase 2 onwards — Next.js + Tailwind CSS**

- Next.js handles routing between screens: Onboarding → Plans → Dashboard
- Tailwind CSS for fast, responsive UI — no CSS from scratch
- Works as a PWA — gig workers access via mobile browser without installing an app
- Deployed on Vercel (free tier)

### Backend

**Python FastAPI**

- Same language as ML — Python — so ML models integrate natively
- FastAPI auto-generates REST API docs
- Key routes: worker registration, weekly policy creation, weather/AQI trigger polling (every 30 mins), and claim processing with fraud validation

### Database

**PostgreSQL + Supabase**

- Supabase provides free hosted PostgreSQL with a dashboard UI
- Built-in auth (login/signup) — no need to build authentication
- Four core tables: **workers** (profile, UPI, earnings tier), **policies** (active weekly coverage per worker), **claims** (trigger type, payout amount, fraud score, status), and **disruption_log** (all API-detected events by city and timestamp)

### ML / AI

**Python + scikit-learn**

- Random Forest for premium risk scoring
- Isolation Forest for fraud/anomaly detection
- No GPU needed — runs on any laptop
- Phase 1: mock outputs + model architecture defined
- Phase 2: trained on synthetic historical data

### Weather & AQI Triggers

**OpenWeatherMap API + AQICN API**

- OpenWeatherMap free tier: real-time rain (mm), temperature, weather alerts by city
- AQICN free tier: real-time AQI by city
- Both are simple REST APIs, integrate in under 30 minutes
- Polled every 30 minutes via a FastAPI background task

### Payments (Phase 3)

**Razorpay Test Mode**

- Sandbox/test mode simulates UPI payments without real money
- Demonstrates full payout flow in the demo
- Not needed for Phase 1 — mentioned as planned integration

---

## 🖥️ Platform Choice: Web App (PWA)

**Why Web over Mobile App?**

| Consideration            | Web (PWA)              | Native App             |
| ------------------------ | ---------------------- | ---------------------- |
| Installation             | None required          | App Store download     |
| Low bandwidth            | ✅ Optimized           | Depends on app size    |
| Development speed        | ✅ Single codebase     | Separate iOS/Android   |
| Update deployment        | ✅ Instant             | App Store review cycle |
| Gig worker accessibility | ✅ Any Android browser | Requires app install   |

Gig workers carry mid-range Android phones with variable data connectivity. A PWA via Next.js means they can use GigShield from any browser link shared on WhatsApp — zero friction onboarding.

---

## 🗺️ End-to-End Application Workflow

The complete journey from a new worker to an automatic payout has four stages:

### Stage 1 — Onboarding

Worker opens GigShield via a WhatsApp link or QR code — no app install needed. The onboarding screen collects their name, city, pincode, delivery platform (Zomato / Swiggy), UPI handle, and declared average weekly earnings. Their delivery partner ID is used for basic verification.

### Stage 2 — Policy Creation

The ML Risk Profiler calculates a personalised weekly premium based on the worker's zone risk score and earnings tier. The worker sees a clear breakdown — _"Your zone: Bengaluru South | Risk: Moderate | Premium: ₹86/week"_ — and selects a coverage tier. On paying via UPI, the policy activates for Mon–Sun of that week.

### Stage 3 — Trigger Monitoring & Auto-Claim

Every 30 minutes, the backend trigger monitor polls OpenWeatherMap and AQICN APIs for the worker's city. If a disruption threshold is crossed (e.g. rainfall > 50mm), the system automatically initiates a claim. The fraud detection layer then runs GPS location validation, activity checks, and duplicate claim prevention — all without any worker action.

### Stage 4 — Instant Payout & Dashboard

If all fraud checks pass, a UPI payout is initiated directly to the worker's registered handle. The worker receives a notification: _"GigShield credited ₹700 for rain disruption — 18 Mar."_ The worker dashboard updates to show coverage status and payout history. The insurer admin dashboard reflects updated loss ratios, trigger events, and any fraud flags raised.

---

## 🗓️ Phased Development Plan

### Phase 1 — Ideation & Foundation (Weeks 1–2) ✅ Current

**Theme: Know Your Delivery Worker**

**Goal:** Define the full product strategy, design the system architecture, and build the frontend skeleton.

| Area                | Deliverable                                                                             |
| ------------------- | --------------------------------------------------------------------------------------- |
| Product             | Persona defined, 3 scenarios written, coverage scope locked                             |
| Premium Model       | Weekly formula designed, coverage tiers set, example calculations validated             |
| Parametric Triggers | 5 triggers defined with thresholds, data sources, and payout percentages                |
| ML Plan             | Random Forest premium model architecture defined, Isolation Forest fraud plan outlined  |
| Frontend            | HTML/CSS/JS prototype — onboarding, premium display, plan selection, dashboard skeleton |
| Docs                | This README + GitHub repo set up                                                        |
| Video               | 2-minute strategy and prototype walkthrough                                             |

---

### Phase 2 — Automation & Protection (Weeks 3–4)

**Theme: Protect Your Worker**

**Goal:** Build the full backend, connect live trigger APIs, and deliver a working end-to-end claims flow.

| Area     | Deliverable                                                                                  |
| -------- | -------------------------------------------------------------------------------------------- |
| Backend  | FastAPI app with routes for registration, policy creation, trigger polling, claim processing |
| Database | Supabase PostgreSQL set up with workers, policies, claims, and disruption_log tables         |
| Triggers | 3–5 automated parametric triggers live with OpenWeatherMap + AQICN real API data             |
| ML       | Dynamic premium calculation using scikit-learn Random Forest trained on synthetic zone data  |
| Claims   | Auto-trigger → fraud check → status update flow working end-to-end                           |
| Frontend | Migrated to Next.js + Tailwind CSS PWA; all pages connected to backend APIs                  |
| Video    | 2-minute working demo video                                                                  |

---

### Phase 3 — Scale & Optimise (Weeks 5–6)

**Theme: Perfect Your Worker**

**Goal:** Add advanced fraud detection, simulated payouts, intelligent dashboards, and prepare the final submission.

| Area             | Deliverable                                                                               |
| ---------------- | ----------------------------------------------------------------------------------------- |
| Fraud Detection  | Isolation Forest trained on synthetic claims data; GPS + activity validation integrated   |
| Payments         | Razorpay test mode integrated — simulated UPI payout demonstrated in demo                 |
| Worker Dashboard | Active coverage status, weekly earnings protected, payout history                         |
| Admin Dashboard  | Loss ratios, predictive analytics for next week's likely disruptions, fraud flag log      |
| Final Demo       | 5-minute video showing simulated rainstorm → auto-claim → payout end-to-end               |
| Pitch Deck       | PDF covering persona, AI architecture, fraud model, and weekly pricing business viability |

---

## 📁 Repository Structure

The repository is organized into two main folders. The `frontend/` folder contains the Next.js app with pages for onboarding, plan selection, and the worker dashboard. The `backend/` folder contains the FastAPI app with separate route files for worker registration, policy management, trigger monitoring, and claims processing. The ML models (premium scorer and fraud detector) live inside a dedicated `ml/` subfolder within the backend. A `.env.example` file documents all required API keys.

---

## 🔑 APIs Used

| API            | Purpose                                | Tier              |
| -------------- | -------------------------------------- | ----------------- |
| OpenWeatherMap | Rain (mm), temperature, weather alerts | Free              |
| AQICN          | Real-time AQI by city                  | Free              |
| Supabase       | Hosted PostgreSQL + Auth               | Free              |
| Razorpay       | UPI payment simulation                 | Sandbox (Phase 3) |

---

## 👥 Team

| Role                 | Responsibility                                        |
| -------------------- | ----------------------------------------------------- |
| Team Lead / Frontend | Next.js UI, onboarding flow, dashboard                |
| Backend Engineer     | FastAPI routes, Supabase integration, trigger polling |
| ML Engineer          | Premium risk model, fraud detection pipeline          |
| Video & Docs         | Demo video, README, pitch deck                        |

---

## ⚠️ What We Explicitly Exclude

Per the problem statement constraints, GigShield does **NOT** cover:

- Health or life insurance
- Vehicle repairs or accident claims
- Any income loss not caused by an external parametric trigger
- Events workers can self-report without API-verifiable evidence

---

## 📌 Key Design Decisions

**1. Weekly pricing over monthly** — Matches gig worker cash flow cycle. Lower psychological cost. Easier to pause and resume.

**2. Parametric over indemnity** — No claims officer needed. No paperwork. Payout is triggered by objective data (rainfall mm, AQI number) — not the worker's subjective report. Eliminates 90% of fraud surface.

**3. Web PWA over native app** — Zero install friction. Works on any Android browser. Shareable via WhatsApp link — the primary communication channel for gig workers in India.

**4. UPI over bank transfer** — Instant. Workers already use PhonePe/GPay. No bank account required. Aligns with how gig platforms already pay them.

**5. Zone-based risk scoring** — Not all of Bengaluru is equally flood-prone. Hyper-local pincode-level risk scoring makes premiums fairer and reduces adverse selection.

---

_GigShield — Built for the backbone of India's delivery economy._
_Guidewire DEVTrails 2026 | Unicorn Chase_
