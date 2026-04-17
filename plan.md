## Objective

Make the backend risk/fraud model production-ready without local real datasets by using:

- robust feature engineering
- live external signals (Weather + AQICN)
- scenario-based validation
- safe fallback behavior
  while preserving existing API compatibility.

## Hard Constraints

- No parallel execution: do exactly one task at a time.
- After each task, report:
  1. What was done
  2. Validation performed
  3. What is needed for next task (if anything)
  4. Known risks
  5. Next task proposal
- Do not proceed to next task until milestone report is produced.
- Use pnpm for all Node workflows.

---

## Task 1 - Model foundation cleanup (single source of truth)

### Goal

Remove model drift and make one canonical risk model path.

### Work

- Keep one canonical risk model module for runtime + scripts.
- Update all imports to that module (`app/main.py`, `scripts/train_ml_model.py`, `scripts/evaluate_model.py`).
- Add model metadata/version payload:
  - `model_version`
  - `feature_schema_version`
  - `trained_at`
  - `training_mode` (synthetic/live/hybrid)
- Add strict input sanitization for prediction:
  - missing values
  - type coercion
  - numeric clipping
  - safe defaults

### Acceptance

- One model implementation path only.
- Backward-compatible response keys preserved.
- No runtime crash on malformed input payloads.

### Milestone Report

- Files changed
- Validation output
- Needs for Task 2 (if any)

---

## Task 2 - External signal integration (Weather API + AQICN API)

### Goal

Use real environmental signals in risk features with safe fallback.

### Work

- Create/normalize integration service (single clean module), e.g.:
  - OpenWeather current + forecast risk extraction
  - AQICN city/feed AQI extraction
- Integrate these signals into risk feature extraction and scoring flow.
- Add resilient fallback modes:
  - API timeout/error -> deterministic mock/default values
  - never block prediction due to provider failure
- Add env-based config:
  - `OPENWEATHER_API_KEY`
  - `AQICN_API_TOKEN`
  - `EXTERNAL_SIGNALS_MODE=live|mock|hybrid`
  - timeout + retry controls

### Acceptance

- Risk prediction works with or without API keys.
- Live signals are used when keys are present.
- Graceful fallback path verified.

### Milestone Report

- Files changed
- Live vs fallback behavior validated
- Needs for Task 3 (API keys, limits, etc.)

---

## Task 3 - Real-world model robustness without historical data

### Goal

Improve reliability despite no local real dataset.

### Work

- Build structured synthetic scenario generator:
  - heavy rain/flood
  - heatwave + high AQI
  - city-season spikes
  - low-signal/missing-data cases
  - adversarial/extreme values
- Add calibrated risk output:
  - bounded score (0-100)
  - confidence band (high/medium/low)
  - reason codes
- Add hybrid guardrail layer:
  - combine ML score + deterministic risk rules
  - conservative escalation to REVIEW when uncertainty is high

### Acceptance

- Stable outputs across stress scenarios.
- No NaN/infinite/out-of-range results.
- Explainable reasoning returned.

### Milestone Report

- Scenario coverage summary
- Metrics and edge-case stability results
- Needs for Task 4

---

## Task 4 - Fraud engine real-flow integration

### Goal

Ensure advanced fraud checks actually execute in `/events/trigger` runtime.

### Work

- Pass structured evidence from trigger flow:
  - `gps_history`
  - `claimed_weather`
  - `actual_weather`
  - `claims_in_area`
  - `historical_validation`
- Ensure advanced detector weights affect final decision.
- Normalize reason outputs and confidence policy.

### Acceptance

- Advanced fraud signals are active in production flow.
- Existing frontend response format remains compatible.

### Milestone Report

- Runtime integration proof
- Backward compatibility status
- Needs for Task 5

---

## Task 5 - Evaluation harness + release readiness

### Goal

Make model behavior auditable and deployment-safe.

### Work

- Add evaluation report generator:
  - scenario pass/fail
  - calibration summary
  - score distribution checks
- Add health/diagnostic endpoint fields:
  - model version
  - external signal mode
  - fallback rate
- Add minimal tests for:
  - API signal fallback
  - feature contract
  - fraud advanced flow

### Acceptance

- Reproducible local report generated.
- Clear operational visibility for demos/real runs.

### Milestone Report

- Report location
- Test results
- Known follow-ups

---

## Final Deliverables

- Production-safe model pipeline with external signals
- Weather + AQICN integration with fallback
- Sequential milestone reports after each task
- Backward-compatible backend APIs

---

Use this as AGENTS.md (or append these rules clearly):

## Core Rule: Package Manager

The agent must use **pnpm** for all JavaScript/Node workflows.

### Mandatory commands

- Install dependencies: `pnpm install`
- Start dev server: `pnpm dev`
- Build project: `pnpm build`
- Start production server: `pnpm start`
- Run scripts/tests/lint: `pnpm <script>`

### Prohibited commands

- Do **not** use `npm install`, `npm run ...`, or `yarn ...`
- Do **not** switch package managers mid-task

## Execution Mode (Strict Sequential)

- Execute exactly **one task at a time** from `plan.md`.
- **Do not perform tasks simultaneously**.
- After completing each task, stop and produce a milestone report before starting next task.

## Milestone Report Format (Required after every task)

1. Task completed
2. Files changed
3. Endpoints/components/modules added or modified
4. Validation performed (commands + key outcome)
5. What is needed for the next task (keys, decisions, dependencies)
6. Known issues/risks
7. Next task proposal

## Backend Modeling Rules

- Preserve backward compatibility with existing API contracts unless explicitly planned.
- Add robust error handling and deterministic fallbacks for all external APIs.
- Bound model outputs and confidence outputs to safe ranges.
- Prefer explainable outputs (reason codes) over opaque scoring.
- If real data is unavailable, use scenario-based validation and synthetic stress testing.

## External API Rules

- Integrate OpenWeather and AQICN with env-driven configuration.
- Never hard-fail prediction on API outage/timeouts.
- Log and surface fallback mode in diagnostics.

## Safety Rules

- Do not run destructive git commands unless explicitly requested.
- Do not delete unrelated files.
- Do not commit secrets or credentials.
- Respect existing project structure and naming conventions.
