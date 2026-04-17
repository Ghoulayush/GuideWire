"use client";

import { useEffect, useMemo, useState } from "react";
import {
  getDashboard,
  getMyClaims,
  getPayoutStatus,
  initiatePayout,
  onboardWorker,
  triggerEvent,
} from "@/lib/api";
import {
  getCurrentSession,
  getCurrentUser,
  getCurrentUserWorkerId,
  saveDeliveryIssue,
  setCurrentUserWorkerId,
} from "@/lib/supabase";
import IssueLocationPicker from "@/components/IssueLocationPicker";

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

const defaultIssueLocation = {
  latitude: 12.9716,
  longitude: 77.5946,
  source: "manual",
  accuracy: null,
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

// 🚀 NEW: Beautiful Fraud Alert Component
function FraudAlert({ fraudResult, onClose }) {
  if (!fraudResult) return null;

  const getScoreColor = (score) => {
    if (score >= 70)
      return { bg: "#ffebee", border: "#d32f2f", text: "#b71c1c" };
    if (score >= 40)
      return { bg: "#fff3e0", border: "#ed6c02", text: "#e65100" };
    return { bg: "#e8f5e9", border: "#2e7d32", text: "#1b5e20" };
  };

  const getActionIcon = (action) => {
    if (action === "REJECT") return "🚫";
    if (action === "REVIEW") return "⚠️";
    return "✅";
  };

  const getActionBadge = (action) => {
    if (action === "REJECT") return "reject-badge";
    if (action === "REVIEW") return "review-badge";
    return "approve-badge";
  };

  const colors = getScoreColor(fraudResult.fraud_score);

  return (
    <div
      className="fraud-alert-container"
      style={{
        background: colors.bg,
        borderLeft: `4px solid ${colors.border}`,
        borderRadius: "16px",
        padding: "1.25rem",
        marginTop: "1.25rem",
        position: "relative",
        animation: "slideIn 0.3s ease-out",
      }}
    >
      <button
        onClick={onClose}
        style={{
          position: "absolute",
          top: "12px",
          right: "12px",
          background: "transparent",
          border: "none",
          fontSize: "1.2rem",
          cursor: "pointer",
          color: "#666",
          padding: "4px 8px",
          borderRadius: "8px",
        }}
        onMouseEnter={(e) => (e.target.style.background = "#eee")}
        onMouseLeave={(e) => (e.target.style.background = "transparent")}
      >
        ✕
      </button>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          flexWrap: "wrap",
          marginBottom: "12px",
        }}
      >
        <span style={{ fontSize: "2rem" }}>
          {getActionIcon(fraudResult.action)}
        </span>
        <h4 style={{ margin: 0, fontSize: "1.1rem", color: colors.text }}>
          AI Fraud Detection Result
        </h4>
        <span className={`fraud-badge ${getActionBadge(fraudResult.action)}`}>
          {fraudResult.action}
        </span>
      </div>

      <div
        style={{
          display: "flex",
          gap: "24px",
          flexWrap: "wrap",
          marginBottom: "12px",
        }}
      >
        <div>
          <span
            style={{
              fontSize: "0.75rem",
              color: "#666",
              textTransform: "uppercase",
            }}
          >
            Fraud Score
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span
              style={{
                fontSize: "1.8rem",
                fontWeight: "bold",
                color: colors.text,
              }}
            >
              {fraudResult.fraud_score}
            </span>
            <span style={{ fontSize: "0.9rem", color: "#666" }}>/ 100</span>
            <div
              className="score-bar"
              style={{
                width: "100px",
                height: "6px",
                background: "#e0e0e0",
                borderRadius: "3px",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${fraudResult.fraud_score}%`,
                  height: "100%",
                  background: colors.border,
                  borderRadius: "3px",
                }}
              ></div>
            </div>
          </div>
        </div>
        <div>
          <span
            style={{
              fontSize: "0.75rem",
              color: "#666",
              textTransform: "uppercase",
            }}
          >
            Confidence
          </span>
          <div
            style={{ fontSize: "1.3rem", fontWeight: "600", color: "#2e7d32" }}
          >
            {fraudResult.confidence || 85}%
          </div>
        </div>
      </div>

      <div style={{ marginBottom: "12px" }}>
        <span
          style={{
            fontSize: "0.75rem",
            color: "#666",
            textTransform: "uppercase",
          }}
        >
          Decision Reason
        </span>
        <p
          style={{
            margin: "4px 0 0 0",
            fontSize: "0.9rem",
            color: "#333",
            background: "rgba(255,255,255,0.7)",
            padding: "8px 12px",
            borderRadius: "10px",
          }}
        >
          {fraudResult.final_decision ||
            fraudResult.reasons?.join(", ") ||
            "No fraud detected"}
        </p>
      </div>

      {fraudResult.detector_results &&
        fraudResult.detector_results.length > 0 && (
          <details style={{ marginTop: "8px" }}>
            <summary
              style={{
                cursor: "pointer",
                fontSize: "0.8rem",
                color: "#666",
                padding: "4px 0",
              }}
            >
              🔍 View detailed detector breakdown (
              {fraudResult.detector_results.length} layers)
            </summary>
            <div style={{ marginTop: "8px", fontSize: "0.8rem" }}>
              {fraudResult.detector_results.map((d, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "6px 0",
                    borderBottom: "1px solid rgba(0,0,0,0.05)",
                  }}
                >
                  <span style={{ fontWeight: "500" }}>{d.detector_name}:</span>
                  <div
                    style={{
                      display: "flex",
                      gap: "12px",
                      alignItems: "center",
                    }}
                  >
                    <span
                      style={{
                        color:
                          d.fraud_score >= 70
                            ? "#d32f2f"
                            : d.fraud_score >= 40
                              ? "#ed6c02"
                              : "#2e7d32",
                      }}
                    >
                      score: {d.fraud_score}
                    </span>
                    <span className={`mini-badge ${d.action?.toLowerCase()}`}>
                      {d.action}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </details>
        )}

      <style jsx>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
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
  const [fraudResult, setFraudResult] = useState(null);
  const [issueLocation, setIssueLocation] = useState(defaultIssueLocation);
  const [workerLinkStatus, setWorkerLinkStatus] = useState("");
  const [myClaims, setMyClaims] = useState([]);
  const [payoutInfo, setPayoutInfo] = useState(null);
  const [latestClaimTimeline, setLatestClaimTimeline] = useState([]);
  const [riskAlerts, setRiskAlerts] = useState([]);

  const metrics = dashboard?.metrics;

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

  async function refreshMyClaims() {
    const session = await getCurrentSession();
    const token = session?.access_token;
    if (!token) {
      setMyClaims([]);
      return;
    }

    const response = await getMyClaims(token);
    if (response?.error) {
      setMyClaims([]);
      return;
    }

    setMyClaims(Array.isArray(response?.items) ? response.items : []);
  }

  useEffect(() => {
    async function load() {
      try {
        await Promise.all([refreshDashboard(), refreshMyClaims()]);
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
      const linkResult = await setCurrentUserWorkerId(payload.worker_id);
      if (linkResult?.ok) {
        setWorkerLinkStatus(`Linked your account to worker ${payload.worker_id}`);
      }
      setNotice(result.message);
      setEventForm((current) => ({
        ...current,
        worker_id: workerForm.worker_id,
      }));
      await refreshDashboard();
      await refreshMyClaims();
    } catch (err) {
      setError(err.message || "Worker onboarding failed");
    } finally {
      setBusy("");
    }
  }

  useEffect(() => {
    async function loadWorkerLinkStatus() {
      const workerId = await getCurrentUserWorkerId();
      if (workerId) {
        setWorkerLinkStatus(`Your account is linked to worker ${workerId}`);
      }
    }

    loadWorkerLinkStatus();
  }, []);

  async function submitEvent(event) {
    event.preventDefault();
    setBusy("event");
    setError("");
    setNotice("");
    setFraudResult(null);

    try {
      const payload = {
        ...eventForm,
        severity: Number(eventForm.severity),
        issue_location: issueLocation,
      };

      const result = await triggerEvent(payload);

      const currentUser = await getCurrentUser();
      await saveDeliveryIssue({
        ...payload,
        user_id: currentUser?.id,
        reporter_email: currentUser?.email,
        backend_message: result.message,
        triggered: !result.has_error,
        payout_amount: result.fraud_data?.action === "REJECT" ? 0 : undefined,
        latitude: issueLocation.latitude,
        longitude: issueLocation.longitude,
        location_source: issueLocation.source,
        location_accuracy: issueLocation.accuracy,
      });

      setNotice(result.message);

      // 🚀 NEW: Capture fraud detection result
      if (result.fraud_data) {
        setFraudResult(result.fraud_data);
      }
      setLatestClaimTimeline(Array.isArray(result.claim_timeline) ? result.claim_timeline : []);
      setRiskAlerts(Array.isArray(result.risk_alerts) ? result.risk_alerts : []);

      await refreshDashboard();
      await refreshMyClaims();
    } catch (err) {
      setError(err.message || "Event trigger failed");
    } finally {
      setBusy("");
    }
  }

  async function startPayout(claim) {
    setBusy("payout");
    setError("");
    setNotice("");
    try {
      const amount = Number(claim.approved_payout || 0);
      if (amount <= 0) {
        throw new Error("This claim has no payout amount");
      }

      const result = await initiatePayout({
        worker_id: claim.worker_id || eventForm.worker_id,
        claim_id: claim.claim_id,
        amount,
      });

      setPayoutInfo(result);
      setNotice(`Payout initiated. Transaction ID: ${result.transaction_id}`);
    } catch (err) {
      setError(err.message || "Payout initiation failed");
    } finally {
      setBusy("");
    }
  }

  useEffect(() => {
    if (!payoutInfo?.transaction_id || payoutInfo.status === "completed") {
      return;
    }

    const timer = setInterval(async () => {
      try {
        const latest = await getPayoutStatus(payoutInfo.transaction_id);
        setPayoutInfo(latest);
      } catch {
      }
    }, 2000);

    return () => clearInterval(timer);
  }, [payoutInfo]);

  return (
    <main className="page-shell">
      <section className="hero-panel">
        <div className="hero-copy">
          <p className="kicker">GuideWire DevTrails 2026</p>
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
        <MetricCard
          title="Earnings Protected"
          value={`₹${myClaims
            .filter((c) => {
              if (!c.created_at) return false;
              const created = new Date(c.created_at);
              const now = new Date();
              return (
                created.getFullYear() === now.getFullYear() &&
                created.getMonth() === now.getMonth() &&
                Number(c.approved_payout || 0) > 0
              );
            })
            .reduce((sum, c) => sum + Number(c.approved_payout || 0), 0)
            .toFixed(2)}`}
          help="Payouts received this month"
        />
        <MetricCard
          title="Active Coverage"
          value={`₹${dashboard?.current_policy?.coverage_per_week ?? 0}`}
          help="Current weekly coverage amount"
        />
        <MetricCard
          title="Coverage Used"
          value={`${(() => {
            const coverageLimit = Number(dashboard?.current_policy?.coverage_per_week || 0);
            const payoutsReceived = myClaims.reduce((sum, c) => sum + Number(c.approved_payout || 0), 0);
            if (!coverageLimit) return 0;
            return Math.min(100, Math.round((payoutsReceived / coverageLimit) * 100));
          })()}%`}
          help="Payouts received vs coverage limit"
        />
      </section>

      <section className="status-panel">
        <p className="metric-title">Coverage Progress</p>
        {(() => {
          const coverageLimit = Number(dashboard?.current_policy?.coverage_per_week || 0);
          const payoutsReceived = myClaims.reduce((sum, c) => sum + Number(c.approved_payout || 0), 0);
          const usedPct = coverageLimit ? Math.min(100, (payoutsReceived / coverageLimit) * 100) : 0;
          return (
            <>
              <div className="score-bar" style={{ width: "100%", height: "10px", background: "#e0e0e0", borderRadius: "6px", overflow: "hidden" }}>
                <div
                  style={{ width: `${usedPct}%`, height: "100%", background: "linear-gradient(140deg, #0e5a8a, #f25c3a)", borderRadius: "6px" }}
                />
              </div>
              <p style={{ marginTop: "0.45rem" }}>
                ₹{payoutsReceived.toFixed(2)} used out of ₹{coverageLimit.toFixed(2)}
              </p>
            </>
          );
        })()}
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

          <IssueLocationPicker
            value={issueLocation}
            onChange={setIssueLocation}
          />

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
        {workerLinkStatus && <p className="notice">{workerLinkStatus}</p>}
        {error && <p className="error">{error}</p>}
      </section>

      {payoutInfo && (
        <section className="status-panel">
          <p>
            <strong>Instant Payout</strong>
          </p>
          <p>
            Transaction ID: <strong>{payoutInfo.transaction_id}</strong>
          </p>
          <p>
            Status: <span className={`status-pill status-${String(payoutInfo.status || "").toLowerCase()}`}>{payoutInfo.status}</span>
          </p>
          <p>{payoutInfo.confirmation_message}</p>
          {payoutInfo.qr_image_url && (
            <div style={{ marginTop: "0.6rem", display: "grid", gap: "0.45rem" }}>
              <img
                src={payoutInfo.qr_image_url}
                alt="UPI payout QR"
                width="180"
                height="180"
                style={{ borderRadius: "12px", border: "1px solid rgba(26, 30, 36, 0.15)" }}
              />
              <small style={{ wordBreak: "break-all", color: "rgba(26, 30, 36, 0.7)" }}>
                UPI URI: {payoutInfo.upi_uri}
              </small>
            </div>
          )}
        </section>
      )}

      {/* 🚀 NEW: Fraud Alert Display */}
      <FraudAlert
        fraudResult={fraudResult}
        onClose={() => setFraudResult(null)}
      />

      <section className="tables-grid">
        <article className="table-card">
          <h3>Claim Timeline</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Stage</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {(latestClaimTimeline.length ? latestClaimTimeline : myClaims[myClaims.length - 1]?.timeline || []).map((item, idx) => (
                  <tr key={`${item.stage}-${idx}`}>
                    <td className="cap">{item.stage}</td>
                    <td>{item.at || "Pending"}</td>
                  </tr>
                ))}
                {!latestClaimTimeline.length && !(myClaims[myClaims.length - 1]?.timeline || []).length && (
                  <tr>
                    <td colSpan={2}>No timeline available yet</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </article>

        <article className="table-card">
          <h3>Risk Alerts</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Alert</th>
                </tr>
              </thead>
              <tbody>
                {riskAlerts.map((alert, idx) => (
                  <tr key={`${alert}-${idx}`}>
                    <td>{alert}</td>
                  </tr>
                ))}
                {!riskAlerts.length && (
                  <tr>
                    <td>No active weather risk alerts</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </article>
      </section>

      <section className="tables-grid">
        <article className="table-card">
          <h3>My Recent Claims</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Claim ID</th>
                  <th>Status</th>
                  <th>Payout</th>
                  <th>Instant Payout</th>
                </tr>
              </thead>
              <tbody>
                {myClaims
                  .slice(-8)
                  .reverse()
                  .map((item) => (
                    <tr key={item.claim_id}>
                      <td>{item.claim_id}</td>
                      <td>
                        <span
                          className={`status-pill status-${String(item.status || "").toLowerCase()}`}
                        >
                          {item.status}
                        </span>
                      </td>
                      <td>₹{item.approved_payout}</td>
                      <td>
                        <button
                          type="button"
                          disabled={busy === "payout" || Number(item.approved_payout || 0) <= 0}
                          onClick={() => startPayout(item)}
                        >
                          {busy === "payout" ? "Processing..." : "Pay via UPI"}
                        </button>
                      </td>
                    </tr>
                  ))}
                {!myClaims.length && (
                  <tr>
                    <td colSpan={4}>No claims found for your account yet</td>
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
