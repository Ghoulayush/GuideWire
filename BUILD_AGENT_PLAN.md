Goal
Stabilize deployed production stack (Vercel frontend + Render backend + Supabase DB), remove UX bugs, and confirm end-to-end reliability before new feature expansion.
## Deployment Context (Current)
- Frontend: deployed on Vercel
- Backend: deployed on Render
- DB target: Supabase Postgres via `DATABASE_URL` (backend)
- Auth: Supabase session-based (frontend)
- Payments: Razorpay test mode integration present
## Non-Negotiable Execution Rules
1. Work on exactly ONE task at a time.
2. Do not start next task until user explicitly replies: `NEXT`.
3. After each task, stop and report:
   - changed files
   - what works now
   - verification run + result
   - required inputs/secrets for next task
4. If blocked, ask only minimum required question(s), then wait.
5. Keep responses short (max 10 bullets).
6. Prefer fixing production-impact issues first; defer new features until stability checks pass.
## Task Order (Sequential Only)
- T1: Deployed environment smoke audit
- T2: UI spacing and collision fixes
- T3: Remove duplicate post-login navbar
- T4: Dynamic navbar by auth + active subscription state
- T5: Razorpay production-path debugging (test mode)
- T6: Map location detection reliability improvements
- T7: Next.js workspace/lockfile warning fix
- T8: Backend persistence verification on Supabase
- T9: Test suite alignment and CI sanity
- T10: Final go/no-go checklist for production hardening
## Task Specs
### T1 — Deployed environment smoke audit
**Deliverable**
- Verify frontend->backend connectivity in deployed URLs.
- Verify `/health` reports expected mode and service readiness.
**Acceptance**
- Frontend can hit deployed backend API.
- Core routes respond without CORS/network errors.
**Stop and wait for `NEXT`.**
---
### T2 — UI spacing and collision fixes
**Deliverable**
- Fix button/text/card spacing collisions in deployed UI (desktop + mobile).
**Acceptance**
- No visible overlap/collision across auth, home, dashboard, subscription, admin.
**Stop and wait for `NEXT`.**
---
### T3 — Remove duplicate post-login navbar
**Deliverable**
- Keep only one navigation system after login.
- Remove secondary tab strip above dashboard boxes.
**Acceptance**
- Logged-in views show only intended top navbar.
**Stop and wait for `NEXT`.**
---
### T4 — Dynamic navbar by auth + active plan state
**Deliverable**
- Logged-out: `About`, `Plans`, `Login`
- Logged-in, no active plan: `Home`, `Dashboard`, `Plans`
- Logged-in, active plan: `Home`, `Dashboard`, `Simulation` (hide `Plans`)
**Acceptance**
- `About` hidden after login.
- Nav switches correctly when subscription status changes.
**Stop and wait for `NEXT`.**
---
### T5 — Razorpay debugging (test mode)
**Deliverable**
- Validate full flow on deployed stack:
  - create order
  - checkout popup
  - verify signature
  - subscription status update
- Ensure no accidental mock fallback when keys exist.
**Acceptance**
- Successful test payment marks subscription `ACTIVE`.
- Errors are user-readable and traceable in logs.
**Needs**
- Render env: `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`
- Vercel env: `NEXT_PUBLIC_RAZORPAY_KEY_ID`
**Stop and wait for `NEXT`.**
---
### T6 — Map geolocation reliability
**Deliverable**
- Improve detect-location flow with clearer success/failure UX.
- Keep manual correction path (pin drag/click + lat/lng edit).
**Acceptance**
- Detect button gives accurate status message.
- User can correct location before submit every time.
**Stop and wait for `NEXT`.**
---
### T7 — Next.js warning fix
**Deliverable**
- Resolve workspace root/lockfile warning via repo-consistent config strategy.
**Acceptance**
- Build/deploy logs no longer show root/lockfile inference warning.
**Stop and wait for `NEXT`.**
---
### T8 — Backend persistence verification on Supabase
**Deliverable**
- Confirm backend writes to Supabase Postgres tables and survives backend restart.
- Verify workers/policies/claims/subscriptions persist.
**Acceptance**
- Data remains after Render restart.
- `/health` reports database mode.
- Supabase table rows match API operations.
**Stop and wait for `NEXT`.**
---
### T9 — Test suite alignment and CI sanity
**Deliverable**
- Reconcile known failing/stale tests with current API surface.
- Ensure focused tests pass and document expected skips/failures.
**Acceptance**
- Core backend/frontend checks pass.
- Any intentionally failing legacy tests are documented with reason.
**Stop and wait for `NEXT`.**
---
### T10 — Final production hardening checkpoint
**Deliverable**
- Provide go/no-go report with risks and remaining blockers.
- List minimal must-fix items before scaling or app conversion.
**Acceptance**
- Clear production readiness decision with evidence.
**Stop after completion.**
## Required Response Format After Each Task
1) Status: DONE / BLOCKED
2) Files changed
3) What is working now
4) Verification run + result
5) Inputs needed for next task
6) Risks/notes (short)
7) `Reply NEXT to continue`
