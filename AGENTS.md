## Repo Map (what actually runs)
- Backend runtime: `app/main.py` (FastAPI app, startup hooks, all API routes).
- Frontend runtime: `frontend/` (Next.js app router).
- Fraud/ML logic: `app/services/` and `app/services/fraud/`.
- Training/util scripts: `scripts/`.
- Tests: `tests/`.

## Commands You Should Actually Use
- Backend dev server: `uvicorn app.main:app --reload`
- Install deps: `pnpm install`
- Frontend dev server: `cd frontend && pnpm run dev`
- Frontend checks: `cd frontend && pnpm run lint && pnpm run build`
- Backend smoke check (server must already be running): `python scripts/check_endpoints.py`
- Focused backend tests: `python -m pytest tests/test_fraud_ensemble.py`
- Run all tests (if env has deps): `python -m pytest tests`

## High-Impact Gotchas
- `app/main.py` stores state in-memory (`WORKERS`, `POLICIES`, `CLAIMS`, etc.); restarting backend clears data.
- Startup in `app/main.py` auto-loads/trains model files in `models/` and starts a 30-minute background monitor.
- Frontend API base URL comes from `NEXT_PUBLIC_API_URL` in `frontend/src/lib/api.js` (default `http://localhost:8000`).
- Runtime risk model import is `app/services/ml_risk.py`; do not confuse with `app/services/ml_risk_model.py` used by some training scripts.
- `tests/test_premium_api.py` currently expects `/api/calculate-premium`, but `app/main.py` does not expose that route.
- TensorFlow-heavy fraud tests (`tests/test_tf_detectors.py`) are optional and may skip without TF/model files.
- Treat unrelated stale/conflict files as out-of-scope unless asked (notably `.gitignore`, `app/db.py`, `app/services/weather_api.py`).
