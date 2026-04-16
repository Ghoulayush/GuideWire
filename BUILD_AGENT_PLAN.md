## Goal

Build a production-ready admin dashboard, move global policy/claim visibility to admin, restrict worker claim visibility to only their own claims, and improve frontend visual quality.

## Current Reality (Do Not Assume)

- Admin page exists but currently focuses on workers/subscriptions.
- Worker dashboard currently shows latest policies + recent claims (global data).
- Backend `/claims` and `/policies` are global endpoints.
- Auth is Supabase session on frontend; backend claim access is not yet user-scoped.
- App is already deployed (Vercel + Render + Supabase), so every change must be deployment-safe.

## Non-Negotiable Execution Rules

1. Work on exactly ONE task at a time.
2. Do not start next task until user replies: `NEXT`.
3. After each task, stop and report:
   - files changed
   - what works now
   - verification result
   - required input/secrets for next task
4. If blocked, ask only minimum required question(s), then wait.
5. No parallel implementation across tasks.

## Task Order (Sequential Only)

- T1: Define ownership model for worker claims
- T2: Add backend user-scoped claims/policies endpoints
- T3: Expand admin dashboard to host latest policies + recent claims
- T4: Remove latest policies/recent claims from worker dashboard
- T5: Restrict worker dashboard claims to own records only
- T6: Frontend visual enhancement pass
- T7: QA + regression checks
- T8: Deploy + post-deploy validation checklist

---

### T1 — Ownership model for worker claims

**Deliverable**

- Finalize how an authenticated user maps to worker records.
- Default implementation: map `auth user -> worker_id` via `user_profiles.worker_id` (or a dedicated mapping table if needed).
  **Acceptance**
- Each authenticated user resolves to exactly one worker context for claims visibility.
- Admin can still view cross-worker/global claims.
  **Stop and wait for `NEXT`.**

---

### T2 — Backend user-scoped endpoints

**Deliverable**

- Add user-scoped endpoints (example):
  - `GET /claims/me`
  - `GET /policies/me` (optional but recommended)
- Keep admin/global endpoints:
  - `GET /claims`
  - `GET /policies`
- Enforce filtering server-side (not only frontend filtering).
  **Acceptance**
- Worker API returns only claims linked to that user’s worker_id.
- Global endpoints remain available for admin workflows.
  **Stop and wait for `NEXT`.**

---

### T3 — Admin dashboard data expansion

**Deliverable**

- Move “Latest Policies” and “Recent Claims” tables to admin interface.
- Add sorting, recency limits, and optional filters (status/worker/plan).
  **Acceptance**
- Admin page becomes the source of truth for cross-user policy/claim monitoring.
- Admin can view latest policies and recent claims in one place.
  **Stop and wait for `NEXT`.**

---

### T4 — Remove global policy/claim tables from worker dashboard

**Deliverable**

- Remove global “Latest Policies” + global “Recent Claims” UI blocks from worker dashboard.
- Keep worker-safe metrics and submission actions.
  **Acceptance**
- Worker UI no longer exposes global policy/claim lists.
  **Stop and wait for `NEXT`.**

---

### T5 — Worker-specific claims visibility

**Deliverable**

- Add worker-facing “My Recent Claims” section powered by `/claims/me`.
- Ensure no other users’ claims can appear.
  **Acceptance**
- Worker sees only own recent claims.
- Cross-user claim leakage is not possible via UI or endpoint response.
  **Stop and wait for `NEXT`.**

---

### T6 — Frontend beautification pass

**Deliverable**

- Improve visual quality with intentional design updates:
  - stronger layout hierarchy
  - cleaner spacing and card rhythm
  - consistent typography scale
  - polished table styling and badges
  - responsive improvements for mobile
- Preserve existing brand direction; avoid random redesign drift.
  **Acceptance**
- Admin and worker dashboards look cleaner, more premium, and easier to scan.
- No usability regressions on desktop/mobile.
  **Stop and wait for `NEXT`.**

---

### T7 — QA + regression checks

**Deliverable**

- Run and report:
  - frontend lint + build
  - focused backend tests
  - manual role-based checks (worker vs admin data access)
- Validate claim visibility boundaries.
  **Acceptance**
- All required checks pass.
- Role-based access behavior validated with clear evidence.
  **Stop and wait for `NEXT`.**

---

### T8 — Deploy + post-deploy validation

**Deliverable**

- Deploy frontend and backend updates.
- Validate on production URLs:
  - admin sees global latest policies/claims
  - worker sees only own claims
  - no broken routes/UI
  - metrics and forms still work
    **Acceptance**
- Production behavior matches requirements.
- No data exposure bugs.
  **Stop after completion.**

## Required Response Format After Each Task

1. Status: DONE / BLOCKED
2. Files changed
3. What is working now
4. Verification run + result
5. Inputs needed for next task
6. Risks/notes (short)
7. `Reply NEXT to continue`
