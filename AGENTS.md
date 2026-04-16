## Repo Map (what actually runs)
- Backend runtime: `app/main.py` (FastAPI app, startup hooks, all API routes).
- Backend persistence layer: `app/db.py` + `app/repositories/store.py` (SQLAlchemy-backed storage).
- Frontend runtime: `frontend/` (Next.js app router).
- Fraud/ML logic: `app/services/` and `app/services/fraud/`.
- Training/util scripts: `scripts/`.
- Tests: `tests/`.

## Commands You Should Actually Use
- Backend dev server: `python -m uvicorn app.main:app --reload` (prefer project venv interpreter).
- Install deps: `pnpm install`
- Frontend dev server: `cd frontend && pnpm run dev`
- Frontend checks: `cd frontend && pnpm run lint && pnpm run build`
- Backend smoke check (server must already be running): `python scripts/check_endpoints.py`
- Focused backend tests: `python -m pytest tests/test_fraud_ensemble.py`
- API flow tests (current routes): `python -m pytest tests/test_premium_api.py`
- Run all tests (if env has deps): `python -m pytest tests`

## High-Impact Gotchas
- Backend defaults to DB mode (`USE_DB_PERSISTENCE=true`); data persists only if `DATABASE_URL` is a real Postgres/SQLite connection string.
- Do not set `DATABASE_URL` to Supabase project URL (`https://...supabase.co`); use Supabase Postgres URI (`postgresql://...`).
- DB tables used by backend are namespaced (`gw_workers`, `gw_policies`, `gw_claims`, `gw_subscriptions`, etc.) and are auto-created by `init_db()`.
- Backend keeps in-memory fallback lists only for `USE_DB_PERSISTENCE=false`; avoid assuming restart-safe state in that mode.
- Startup in `app/main.py` auto-loads/trains model files in `models/` and starts a 30-minute background monitor.
- Frontend API base URL comes from `NEXT_PUBLIC_API_URL` in `frontend/src/lib/api.js` (default `http://localhost:8000`).
- Runtime risk model import is `app/services/ml_risk.py`; do not confuse with `app/services/ml_risk_model.py` used by some training scripts.
- Frontend auth source of truth is Supabase session (`frontend/src/lib/supabase.js`), not localStorage auth helpers.
- Post-login navbar is subscription-state aware in `frontend/src/components/SiteHeader.js`.
- TensorFlow-heavy fraud tests (`tests/test_tf_detectors.py`) are optional and may skip without TF/model files.
- Treat unrelated stale/conflict files as out-of-scope unless asked (notably `.gitignore`, `app/services/weather_api.py`).
