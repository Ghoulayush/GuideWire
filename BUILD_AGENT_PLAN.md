## Non-Negotiable Execution Rules

1. Work on exactly ONE task at a time.
2. Do not start next task until user explicitly replies: `NEXT`.
3. After each task, stop and report:
   - changed files
   - what works now
   - verification run + result
   - required secrets/inputs for next task
4. If blocked, ask only the minimum required question(s), then wait.
5. Keep responses short (max 10 bullets).

## Task Order (Sequential Only)

- T1: Post-login app structure (Home, Dashboard, Simulation, Subscription tabs)
- T2: Supabase check/integration (auth + issue storage)
- T3: Razorpay subscription flow
- T4: Admin interface
- T5: OpenMap location picker + auto-detect/fix flow
- T6: UX animations
- T7: Mobile app conversion plan + starter implementation

## Task Specs

### T1 — Post-login structure

**Deliverable**

- Auth redirects to logged-in home shell with tabs: Dashboard, Simulation, Subscription.
- Route protection for authenticated users.
  **Acceptance**
- Login/signup lands on user home.
- Tabs navigate correctly.
- Unauthenticated access redirects to login.
  **Stop after completion and wait for `NEXT`.**

---

### T2 — Supabase integration

**Deliverable**

- Confirm existing Supabase usage; if missing, add it.
- Tell how to setup the supabase database for this project and which free tier database to use and where to input the SUPABASE_URL and SUPABASE_ANON_KEY
- Persist user profile + delivery issue records.
  **Needs from user before/while task**
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- DB schema preference (or use default proposed schema)
  **Acceptance**
- User data persists after refresh/restart.
- Issue submission creates DB record.
  **Stop after completion and wait for `NEXT`.**

---

### T3 — Razorpay subscriptions

**Deliverable**

- Subscription tab wired to Razorpay checkout.
  **Needs from user**
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- plan IDs / amounts / billing cycle
  **Acceptance**
- Test payment works in sandbox.
- Payment status reflected in app.
  **Stop after completion and wait for `NEXT`.**

---

### T4 — Admin interface

**Deliverable**

- Admin login + dashboard for users/issues/subscriptions.
  **Acceptance**
- Admin-only access enforced.
- Admin can view/filter core records.
  **Stop after completion and wait for `NEXT`.**

---

### T5 — OpenMap location flow

**Deliverable**

- Map picker + auto-location detection + manual correction.
- Store corrected coordinates with issue.
  **Needs from user**
- Preferred map stack (Mapbox / Google Maps / Leaflet + OSM)
- API key (if required by provider)
  **Acceptance**
- User can auto-detect and adjust pin before submit.
  **Stop after completion and wait for `NEXT`.**

---

### T6 — Animations

**Deliverable**

- Add purposeful animations on key screens (login, dashboard cards, tab transitions).
  **Acceptance**
- Smooth on mobile + desktop.
- No layout shift or accessibility regressions.
  **Stop after completion and wait for `NEXT`.**

---

### T7 — Convert to app

**Deliverable**

- Mobile conversion approach (PWA-first or React Native/Expo wrapper) + initial implementation.
  **Needs from user**
- Preferred path: `PWA` or `React Native/Expo`
- Target platform: Android / iOS / both
  **Acceptance**
- Build/run instructions provided.
- Core flows usable on selected platform(s).
  **Stop after completion.**

## Required Response Format After Each Task

- Status: DONE / BLOCKED
- Files changed
- Verification performed
- Known risks
- Inputs needed for next task
- Prompt: `Reply NEXT to continue`
  Why this works:
- Very low token overhead.
- Forces checkpoint-based execution.
- Prevents parallel task jumping.
- Makes the agent ask for keys only when needed.
