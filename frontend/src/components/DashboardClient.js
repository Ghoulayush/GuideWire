"use client";

import { useEffect, useMemo, useState } from "react";
import {
  API_BASE_URL,
  getDashboard,
  onboardWorker,
  triggerEvent,
} from "@/lib/api";

const defaultWorker = {
  worker_id: "worker-ravi-001",
  name: "Ravi Kumar",
  city: "Bengaluru",
  pincode: "560001",
  platform: "Swiggy",
  avg_daily_income: "1000",
};

const defaultEvent = {
  worker_id: "worker-ravi-001",
  disruption_type: "environmental",
  severity: "4",
  description: "Heavy rainfall blocked deliveries for 6 hours",
};

function MetricCard({ title, value, help }) {
  return (
    <article className="metric-card">
      <p className="metric-title">{title}</p>
      <p className="metric-value">{value}</p>
      <p className="metric-help">{help}</p>
    </article>
  );
}

export default function DashboardClient({ storyHtml }) {
  const [dashboard, setDashboard] = useState(null);
  const [workerForm, setWorkerForm] = useState(defaultWorker);
  const [eventForm, setEventForm] = useState(defaultEvent);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const metrics = dashboard?.metrics;
  const recentClaims = dashboard?.claims || [];
  const policies = dashboard?.policies || [];

  const disruptionSummary = useMemo(() => {
    const list = metrics?.disruption_counts || [];
    if (!list.length) {
      return "No disruption data yet.";
    }

    return list
      .map((item) => `${item.disruption_type}: ${item.count}`)
      .join(" | ");
  }, [metrics]);

  async function refreshDashboard() {
    setError("");
    const data = await getDashboard();
    setDashboard(data);
  }

  useEffect(() => {
    async function load() {
      try {
        await refreshDashboard();
      } catch (err) {
        setError(err.message || "Could not fetch dashboard data");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  function onWorkerChange(event) {
    const { name, value } = event.target;
    setWorkerForm((previous) => ({ ...previous, [name]: value }));
  }

  function onEventChange(event) {
    const { name, value } = event.target;
    setEventForm((previous) => ({ ...previous, [name]: value }));
  }

  async function submitWorker(event) {
    event.preventDefault();
    setBusy("worker");
    setError("");
    setNotice("");

    try {
      const payload = {
        ...workerForm,
        avg_daily_income: Number(workerForm.avg_daily_income),
      };

      const result = await onboardWorker(payload);
      setNotice(result.message);
      setEventForm((current) => ({
        ...current,
        worker_id: workerForm.worker_id,
      }));
      await refreshDashboard();
    } catch (err) {
      setError(err.message || "Worker onboarding failed");
    } finally {
      setBusy("");
    }
  }

  async function submitEvent(event) {
    event.preventDefault();
    setBusy("event");
    setError("");
    setNotice("");

    try {
      const payload = {
        ...eventForm,
        severity: Number(eventForm.severity),
      };

      const result = await triggerEvent(payload);
      setNotice(result.message);
      await refreshDashboard();
    } catch (err) {
      setError(err.message || "Event trigger failed");
    } finally {
      setBusy("");
    }
  }

  return (
    <main className="page-shell">
      <section className="hero-panel">
        <div className="hero-copy">
          <p className="kicker">GuideWire DevTrails 2026</p>
          <h1>GigShield Parametric Control Center</h1>
          <p>
            Next.js + Pretext frontend connected to your FastAPI backend. Run
            worker onboarding, trigger disruption events, and monitor claim
            outputs in one place.
          </p>
          <span className="api-chip">Backend: {API_BASE_URL}</span>
        </div>
        <div
          className="story-card"
          dangerouslySetInnerHTML={{ __html: storyHtml }}
        />
      </section>

      <section className="metrics-grid">
        <MetricCard
          title="Workers"
          value={metrics?.total_workers ?? 0}
          help="Registered delivery partners"
        />
        <MetricCard
          title="Policies"
          value={metrics?.active_policies ?? 0}
          help="Active weekly covers"
        />
        <MetricCard
          title="Claims"
          value={metrics?.total_claims ?? 0}
          help="Auto-generated claim records"
        />
        <MetricCard
          title="Approved Payout"
          value={`₹${metrics?.total_payout ?? 0}`}
          help="Total disbursed so far"
        />
      </section>

      <section className="forms-grid">
        <form className="form-card" onSubmit={submitWorker}>
          <h2>Onboard Worker</h2>
          <label>
            Worker ID
            <input
              name="worker_id"
              value={workerForm.worker_id}
              onChange={onWorkerChange}
              required
            />
          </label>
          <label>
            Name
            <input
              name="name"
              value={workerForm.name}
              onChange={onWorkerChange}
              required
            />
          </label>
          <label>
            City
            <input
              name="city"
              value={workerForm.city}
              onChange={onWorkerChange}
              required
            />
          </label>
          <label>
            Pincode
            <input
              name="pincode"
              value={workerForm.pincode}
              onChange={onWorkerChange}
              required
            />
          </label>
          <label>
            Platform
            <input
              name="platform"
              value={workerForm.platform}
              onChange={onWorkerChange}
              required
            />
          </label>
          <label>
            Avg Daily Income
            <input
              name="avg_daily_income"
              value={workerForm.avg_daily_income}
              onChange={onWorkerChange}
              type="number"
              min="100"
              step="50"
              required
            />
          </label>
          <button type="submit" disabled={busy === "worker"}>
            {busy === "worker" ? "Saving..." : "Create Worker + Policy"}
          </button>
        </form>

        <form className="form-card" onSubmit={submitEvent}>
          <h2>Trigger Disruption Event</h2>
          <label>
            Worker ID
            <input
              name="worker_id"
              value={eventForm.worker_id}
              onChange={onEventChange}
              required
            />
          </label>
          <label>
            Disruption Type
            <select
              name="disruption_type"
              value={eventForm.disruption_type}
              onChange={onEventChange}
            >
              <option value="environmental">environmental</option>
              <option value="social">social</option>
            </select>
          </label>
          <label>
            Severity (1-5)
            <input
              name="severity"
              value={eventForm.severity}
              onChange={onEventChange}
              type="number"
              min="1"
              max="5"
              required
            />
          </label>
          <label>
            Description
            <textarea
              name="description"
              value={eventForm.description}
              onChange={onEventChange}
              rows={4}
              required
            />
          </label>
          <button type="submit" disabled={busy === "event"}>
            {busy === "event" ? "Submitting..." : "Evaluate Trigger + Claim"}
          </button>
        </form>
      </section>

      <section className="status-panel">
        {loading && <p>Loading dashboard data...</p>}
        {!loading && !error && (
          <p>
            Disruption summary: <strong>{disruptionSummary}</strong>
          </p>
        )}
        {notice && <p className="notice">{notice}</p>}
        {error && <p className="error">{error}</p>}
      </section>

      <section className="tables-grid">
        <article className="table-card">
          <h3>Latest Policies</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Worker</th>
                  <th>Premium</th>
                  <th>Coverage</th>
                </tr>
              </thead>
              <tbody>
                {policies
                  .slice(-5)
                  .reverse()
                  .map((item) => (
                    <tr key={item.policy_id}>
                      <td>{item.worker_id}</td>
                      <td>₹{item.weekly_premium}</td>
                      <td>₹{item.coverage_per_week}</td>
                    </tr>
                  ))}
                {!policies.length && (
                  <tr>
                    <td colSpan={3}>No policies yet</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </article>

        <article className="table-card">
          <h3>Recent Claims</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Worker</th>
                  <th>Status</th>
                  <th>Payout</th>
                </tr>
              </thead>
              <tbody>
                {recentClaims
                  .slice(-8)
                  .reverse()
                  .map((item) => (
                    <tr key={item.claim_id}>
                      <td>{item.worker_id}</td>
                      <td className="cap">{item.status}</td>
                      <td>₹{item.approved_payout}</td>
                    </tr>
                  ))}
                {!recentClaims.length && (
                  <tr>
                    <td colSpan={3}>No claims yet</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </article>
      </section>
    </main>
  );
}
