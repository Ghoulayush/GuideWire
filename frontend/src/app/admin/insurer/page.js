"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import ProtectedAdminRoute from "@/components/ProtectedAdminRoute";
import { getInsurerMetrics } from "@/lib/api";

function MetricCard({ title, value, help }) {
  return (
    <article className="metric-card">
      <p className="metric-title">{title}</p>
      <p className="metric-value">{value}</p>
      <p className="metric-help">{help}</p>
    </article>
  );
}

export default function InsurerDashboardPage() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await getInsurerMetrics();
        setMetrics(data);
      } catch (err) {
        setError(err.message || "Could not load insurer metrics");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  return (
    <ProtectedAdminRoute>
      <main className="home-shell">
        <section className="home-hero admin-header">
          <div>
            <p className="kicker">Insurer Console</p>
            <h1>Loss ratio and reserve planning</h1>
            <p>Live metrics for underwriting and risk operations.</p>
          </div>
          <Link href="/admin" className="login-link">
            Back to Admin
          </Link>
        </section>

        {loading && (
          <section className="home-card">
            <p>Loading insurer metrics...</p>
          </section>
        )}

        {error && (
          <section className="home-card">
            <p className="error">{error}</p>
          </section>
        )}

        {!loading && !error && metrics && (
          <>
            <section className="metrics-grid">
              <MetricCard
                title="Total Premium"
                value={`Rs. ${metrics.total_premium_collected ?? 0}`}
                help="Weekly premium pool collected"
              />
              <MetricCard
                title="Total Payouts"
                value={`Rs. ${metrics.total_payouts ?? 0}`}
                help="Approved and paid claims"
              />
              <MetricCard
                title="Loss Ratio"
                value={`${metrics.loss_ratio ?? 0}%`}
                help="(Total payout / total premium) x 100"
              />
              <MetricCard
                title="Fraud Savings"
                value={`Rs. ${metrics.fraud_prevention_savings ?? 0}`}
                help="Rejected claims amount prevented"
              />
              <MetricCard
                title="Next Week Claims"
                value={metrics.predicted_next_week_claims ?? 0}
                help="Forecasted claims from weather risk"
              />
              <MetricCard
                title="Recommended Reserve"
                value={`Rs. ${metrics.recommended_reserve ?? 0}`}
                help="Expected claims x average payout"
              />
            </section>

            <section className="table-card">
              <h3>High Risk Zones</h3>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>City</th>
                      <th>Rain Probability</th>
                      <th>Expected Claims</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(metrics.high_risk_zones || []).map((zone) => (
                      <tr key={zone.city}>
                        <td>{zone.city}</td>
                        <td>{zone.rain_probability}%</td>
                        <td>{zone.expected_claims}</td>
                      </tr>
                    ))}
                    {(!metrics.high_risk_zones || !metrics.high_risk_zones.length) && (
                      <tr>
                        <td colSpan={3}>No high-risk zones currently detected</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}
      </main>
    </ProtectedAdminRoute>
  );
}
