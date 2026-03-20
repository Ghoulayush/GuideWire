# GigShield: AI-Powered Parametric Income Protection

GigShield is a prototype parametric insurance platform designed for India’s gig-economy delivery partners (Zomato, Swiggy, Zepto, Dunzo, Amazon, etc.). It protects workers against **income loss** caused by external disruptions like extreme weather, pollution, and civic restrictions, while **explicitly excluding** health, life, accident, and vehicle repair coverage.

## Problem It Solves

Gig workers in India are paid per delivery. When external factors such as heat waves, heavy rain, floods, severe pollution, strikes, or curfews halt deliveries, they suddenly lose a significant portion of their weekly income with no safety net. Traditional insurance products focus on health or asset damage, not **short-term income drops**.

GigShield addresses this by:
- Providing **weekly-priced parametric covers** aligned with gig workers’ earning cycles.
- Automatically **triggering payouts** when disruption indicators cross thresholds (no manual claims).
- Using simple **AI-style risk scoring** to personalize premiums based on city, pincode, platform, and income.

## High-Level Flow

1. **Worker onboarding**
   - Fields: worker ID, name, city, pincode, platform (Zomato/Swiggy/Zepto/Dunzo/Amazon), average daily income.
   - Backend converts this into a `RiskInput` and passes it to the risk engine.

2. **AI risk assessment & weekly pricing**
   - Risk engine scores disruption probability using:
     - City risk tier (e.g., Mumbai/Delhi vs tier‑2 cities).
     - Pincode and platform profile (proxy for exposure and activity).
     - Average daily income (earnings capacity).
     - External disruption frequency index (derived/simulated today, can be fed by real APIs later).
   - Produces:
     - Risk score (0–100).
     - Risk band (Low / Medium / High).
     - Suggested **weekly premium**, computed as a % of weekly income.
   - A weekly policy is created automatically with:
     - `weekly_premium` and `coverage_per_week` (typically ~80% of weekly income).

3. **Parametric trigger evaluation**
   - When a disruption occurs (real or simulated), the console records:
     - Worker ID, disruption type (environmental or social), severity (1–5), free‑text description.
   - The trigger engine maps severity to **environmental signals** (rainfall, heat index, AQI, flood alert, curfew) and evaluates rules:
     - Examples: heavy rain or very high heat index, AQI above a threshold, flood alert, or curfew.
   - If rules are met, the engine calculates **payout proportional to daily income**, disruption intensity, and a payout multiplier.

4. **Automatic payout & fraud checks**
   - When a trigger fires:
     - A claim-like payout record is created instantly (no manual claim submission).
     - Fraud engine runs basic anomaly checks:
       - Too many payouts for a worker in a short window.
       - Duplicate payouts for the same disruption event.
       - Claimed vs modelled loss inflation.
     - If high-severity fraud signals appear, the payout is flagged or rejected.

5. **Analytics & monitoring**
   - Analytics dashboard summarizes:
     - Total workers and active policies.
     - Total/approved payouts and total amount paid.
     - Average risk score across the portfolio.
     - Distribution of disruptions by type.
   - This helps insurers or product teams tune thresholds and pricing.

## Architecture Overview

- **Frontend (template-based console)**
  - Mobile-first HTML/CSS dashboard styled as "GigShield".
  - Pages:
    - Main console: onboarding, disruption trigger simulation, portfolio snapshot, worker profile, recent payouts.
    - Analytics: key metrics and disruption breakdown chart (Chart.js).
  - Dark/light theme toggle stored in `localStorage`.

- **Backend (Python FastAPI)**
  - `app/main.py`: HTTP routes, in-memory data store for workers, policies, events, and payouts.
  - `app/schemas.py`: Pydantic models for risk profiles, disruptions, claims/payouts, analytics metrics.
  - `app/services/risk.py`: AI-style risk scoring and weekly premium recommendation.
  - `app/services/triggers.py`: Parametric trigger rules using disruption type + synthetic or real signals.
  - `app/services/fraud.py`: Simple fraud detection heuristics.
  - `app/services/analytics.py`: Aggregates metrics for dashboards.
  - `app/services/integrations.py`: Mocked external data fetcher (ready for real Weather/AQI/Civic APIs).

## How It Demonstrates the Hackathon Idea

- **AI-powered pricing**: even though the model is heuristic, it behaves like an ML risk score—combining multiple factors into a 0–100 score and dynamic weekly premium.
- **Parametric automation**: payouts are driven purely by predefined rules on disruption parameters, not by manual claim assessment.
- **Zero manual claims**: workers never file claims; the system monitors triggers and pays out automatically when thresholds are breached.
- **Fraud prevention**: simple but clear checks show how parametric products can still defend against abuse.
- **Weekly financial model**: premiums and coverage are explicitly weekly, matching gig workers’ earning cadence.

This makes GigShield a concise but end-to-end demonstration of how AI‑powered parametric insurance can protect gig workers’ income in real time during disruptive events.