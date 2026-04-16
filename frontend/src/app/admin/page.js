"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import ProtectedAdminRoute from "@/components/ProtectedAdminRoute";
import { getAdminSession, logoutAdmin } from "@/lib/admin";
import { getAllSubscriptions, getAllWorkers } from "@/lib/api";

export default function AdminPage() {
  const router = useRouter();
  const [workers, setWorkers] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const adminSession = useMemo(() => getAdminSession(), []);

  async function loadData(filterStatus = "") {
    setError("");
    setLoading(true);
    try {
      const [workersData, subsData] = await Promise.all([
        getAllWorkers(),
        getAllSubscriptions(filterStatus),
      ]);
      setWorkers(Array.isArray(workersData) ? workersData : []);
      setSubscriptions(Array.isArray(subsData.items) ? subsData.items : []);
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
                          <td>{sub.status}</td>
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
