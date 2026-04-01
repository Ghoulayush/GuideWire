const plans = [
  {
    name: "Essential",
    price: "₹49/week",
    payout: "Up to ₹500 per event",
    details: "Great for part-time workers with predictable city routes.",
  },
  {
    name: "Growth",
    price: "₹69/week",
    payout: "Up to ₹850 per event",
    details: "Balanced protection for full-time riders across mixed zones.",
    featured: true,
  },
  {
    name: "Shield Max",
    price: "₹99/week",
    payout: "Up to ₹1500 per event",
    details: "Highest cover for high-intensity metro and monsoon exposure.",
  },
];

export default function PlansPage() {
  return (
    <main className="plans-shell">
      <section className="plans-hero">
        <p className="kicker">Subscription Plans</p>
        <h1>Pick weekly protection that matches your earning rhythm.</h1>
      </section>

      <section className="plans-grid">
        {plans.map((plan) => (
          <article
            key={plan.name}
            className={`plan-card${plan.featured ? " featured" : ""}`}
          >
            <h2>{plan.name}</h2>
            <p className="plan-price">{plan.price}</p>
            <p className="plan-payout">{plan.payout}</p>
            <p>{plan.details}</p>
            <button type="button">Choose Plan</button>
          </article>
        ))}
      </section>
    </main>
  );
}
