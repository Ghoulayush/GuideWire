import Link from "next/link";

const highlights = [
  {
    title: "Parametric Engine",
    body: "Payouts trigger on verified disruption signals like extreme rainfall, AQI, and curfew events.",
  },
  {
    title: "Weekly Coverage",
    body: "Premium bands are tuned for gig-worker cashflow, so protection feels affordable and predictable.",
  },
  {
    title: "AI Fraud Screen",
    body: "Claim workflows run through anomaly checks before approvals, reducing bad payouts while keeping speed.",
  },
];

export default function Home() {
  return (
    <main className="landing-shell">
      <section className="landing-hero">
        <p className="kicker">GigShield Product</p>
        <h1>
          Income insurance designed for delivery workers in volatile cities.
        </h1>
        <p className="landing-subtext">
          Inspired by clean, editorial SaaS storytelling, this frontend
          separates product narrative, access control, operational dashboard,
          and plan selection into focused pages.
        </p>
        <div className="cta-row">
          <Link href="/auth" className="cta-primary">
            Login / Sign Up
          </Link>
          <Link href="/plans" className="cta-ghost">
            View Plans
          </Link>
          <Link href="/dashboard" className="cta-ghost">
            Open Dashboard
          </Link>
        </div>
      </section>

      <section className="highlight-grid">
        {highlights.map((item) => (
          <article className="highlight-card" key={item.title}>
            <h2>{item.title}</h2>
            <p>{item.body}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
