"use client";

import Link from "next/link";
import ProtectedRoute from "@/components/ProtectedRoute";

const bullets = [
  "Use the dashboard trigger flow for live AI event simulation.",
  "Review fraud score bands: approve (<40), review (40-69), reject (>=70).",
  "Track output messages from backend claim evaluation responses.",
];

export default function SimulationPage() {
  return (
    <ProtectedRoute>
      <main className="home-shell">
        <section className="home-hero">
          <p className="kicker">Simulation</p>
          <h1>AI Simulation Workspace</h1>
          <p>
            This tab centralizes simulation guidance while the execution flow
            runs through the dashboard controls.
          </p>
        </section>

        <section className="home-card simulation-card">
          <h2>How to run a simulation</h2>
          <ul>
            {bullets.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <Link href="/dashboard" className="cta-primary">
            Go to Dashboard Simulation Controls
          </Link>
        </section>
      </main>
    </ProtectedRoute>
  );
}
