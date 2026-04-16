"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import ProtectedAdminRoute from "@/components/ProtectedAdminRoute";
import { getAdminSession, logoutAdmin } from "@/lib/admin";
import {
  getAllClaims,
  getAllPolicies,
  getAllSubscriptions,
  getAllWorkers,
} from "@/lib/api";

export default function AdminPage() {
  const router = useRouter();
  const [workers, setWorkers] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [claims, setClaims] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const adminSession = useMemo(() => getAdminSession(), []);

  async function loadData(filterStatus = "") {
    setError("");
    setLoading(true);
    try {
      const [workersData, subsData, policiesData, claimsData] = await Promise.all([
        getAllWorkers(),
        getAllSubscriptions(filterStatus),
        getAllPolicies(),
        getAllClaims(),
      ]);
      setWorkers(Array.isArray(workersData) ? workersData : []);
      setSubscriptions(Array.isArray(subsData.items) ? subsData.items : []);
      setPolicies(Array.isArray(policiesData) ? policiesData : []);
      setClaims(Array.isArray(claimsData) ? claimsData : []);
    } catch (err) {
      setError(err.message || "Could not load admin data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData("");
  }, []);

  async function applyFilter(nextStatus) {
    setStatusFilter(nextStatus);
    await loadData(nextStatus);
  }

  function onLogout() {
    logoutAdmin();
    router.replace("/admin/login");
  }

  return (
    <ProtectedAdminRoute>
      <main className="home-shell">
        <section className="home-hero admin-header">
          <div>
            <p className="kicker">Admin Console</p>
            <h1>Operations dashboard</h1>
            <p>Signed in as: {adminSession?.email || "admin"}</p>
          </div>
          <button type="button" className="logout-btn" onClick={onLogout}>
            Logout Admin
          </button>
        </section>

        {loading && (
          <section className="home-card">
            <p>Loading admin data...</p>
          </section>
        )}

        {error && (
          <section className="home-card">
            <p className="error">{error}</p>
          </section>
        )}

        {!loading && !error && (
          <>
            <section className="metrics-grid">
              <article className="metric-card">
                <p className="metric-title">Total Workers</p>
                <p className="metric-value">{workers.length}</p>
              </article>
              <article className="metric-card">
                <p className="metric-title">Subscriptions</p>
                <p className="metric-value">{subscriptions.length}</p>
              </article>
              <article className="metric-card">
                <p className="metric-title">Policies</p>
                <p className="metric-value">{policies.length}</p>
              </article>
              <article className="metric-card">
                <p className="metric-title">Claims</p>
                <p className="metric-value">{claims.length}</p>
              </article>
              <article className="metric-card">
                <p className="metric-title">Active Subscriptions</p>
                <p className="metric-value">
                  {subscriptions.filter((item) => item.status === "ACTIVE").length}
                </p>
              </article>
            </section>

            <section className="home-card admin-filter-row">
              <p className="metric-title">Filter subscription status</p>
              <div className="admin-filter-buttons">
                <button type="button" onClick={() => applyFilter("")}>All</button>
                <button type="button" onClick={() => applyFilter("ACTIVE")}>Active</button>
                <button type="button" onClick={() => applyFilter("CREATED")}>Created</button>
                <button type="button" onClick={() => applyFilter("CREATED_MOCK")}>Mock</button>
              </div>
              <p>Current filter: {statusFilter || "All"}</p>
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
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {policies
                        .slice(-10)
                        .reverse()
                        .map((policy) => (
                          <tr key={policy.policy_id}>
                            <td>{policy.worker_id}</td>
                            <td>Rs. {policy.weekly_premium}</td>
                            <td>Rs. {policy.coverage_per_week}</td>
                            <td>
                              <span
                                className={
                                  policy.active
                                    ? "status-pill status-success"
                                    : "status-pill status-muted"
                                }
                              >
                                {policy.active ? "active" : "inactive"}
                              </span>
                            </td>
                          </tr>
                        ))}
                      {!policies.length && (
                        <tr>
                          <td colSpan={4}>No policies available</td>
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
                      {claims
                        .slice(-12)
                        .reverse()
                        .map((claim) => (
                          <tr key={claim.claim_id}>
                            <td>{claim.worker_id}</td>
                            <td>
                              <span
                                className={`status-pill status-${String(claim.status || "").toLowerCase()}`}
                              >
                                {claim.status}
                              </span>
                            </td>
                            <td>Rs. {claim.approved_payout}</td>
                          </tr>
                        ))}
                      {!claims.length && (
                        <tr>
                          <td colSpan={3}>No claims available</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </article>

              <article className="table-card">
                <h3>Workers</h3>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Worker ID</th>
                        <th>Name</th>
                        <th>City</th>
                        <th>Platform</th>
                      </tr>
                    </thead>
                    <tbody>
                      {workers.map((worker) => (
                        <tr key={worker.worker_id}>
                          <td>{worker.worker_id}</td>
                          <td>{worker.name}</td>
                          <td>{worker.city}</td>
                          <td>{worker.platform}</td>
                        </tr>
                      ))}
                      {!workers.length && (
                        <tr>
                          <td colSpan={4}>No workers available</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </article>

              <article className="table-card">
                <h3>Subscriptions</h3>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Email</th>
                        <th>Plan</th>
                        <th>Status</th>
                        <th>Mode</th>
                      </tr>
                    </thead>
                    <tbody>
                      {subscriptions.map((sub) => (
                        <tr key={sub.id}>
                          <td>{sub.customer_email}</td>
                          <td>{sub.plan_id}</td>
                          <td>
                            <span
                              className={`status-pill status-${String(sub.status || "").toLowerCase()}`}
                            >
                              {sub.status}
                            </span>
                          </td>
                          <td>{sub.mode}</td>
                        </tr>
                      ))}
                      {!subscriptions.length && (
                        <tr>
                          <td colSpan={4}>No subscriptions available</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </article>
            </section>
          </>
        )}
      </main>
    </ProtectedAdminRoute>
  );
}
