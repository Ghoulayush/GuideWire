"use client";

import Link from "next/link";
import ProtectedRoute from "@/components/ProtectedRoute";

const tabs = [
  {
    title: "Dashboard",
    href: "/dashboard",
    description: "Monitor workers, policies, and claim outcomes.",
  },
  {
    title: "Simulation",
    href: "/simulation",
    description: "Run AI event simulations and preview fraud decisions.",
  },
  {
    title: "Subscription",
    href: "/subscription",
    description: "Review coverage plans and manage your weekly protection.",
  },
];

export default function HomePage() {
  return (
    <ProtectedRoute>
      <main className="home-shell">
        <section className="home-hero">
          <p className="kicker">Logged-in Workspace</p>
          <h1>Welcome to your GigShield home.</h1>
          <p>
            Choose a workspace tab to manage live insurance operations for gig
            workers.
          </p>
        </section>

        <section className="home-grid">
          {tabs.map((tab) => (
            <article className="home-card" key={tab.title}>
              <h2>{tab.title}</h2>
              <p>{tab.description}</p>
              <Link className="cta-primary" href={tab.href}>
                Open {tab.title}
              </Link>
            </article>
          ))}
        </section>
      </main>
    </ProtectedRoute>
  );
}
