"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ProtectedRoute from "@/components/ProtectedRoute";
import UserTabs from "@/components/UserTabs";
import {
  createSubscriptionOrder,
  getSubscriptionStatus,
  loadRazorpayScript,
  RAZORPAY_KEY_ID,
  verifySubscriptionPayment,
} from "@/lib/api";
import { getCurrentUser, onAuthStateChange } from "@/lib/supabase";

const planPreview = [
  { id: "essential", name: "Essential", price: 49 },
  { id: "growth", name: "Growth", price: 69 },
  { id: "shield_max", name: "Shield Max", price: 99 },
];

export default function SubscriptionPage() {
  const [busyPlan, setBusyPlan] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [statusLoading, setStatusLoading] = useState(false);
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    let mounted = true;

    async function bootstrapUser() {
      const user = await getCurrentUser();
      if (!mounted) return;
      setCurrentUser(user);
    }

    bootstrapUser();

    const { data } = onAuthStateChange((_event, session) => {
      if (!mounted) return;
      setCurrentUser(session?.user || null);
    });

    return () => {
      mounted = false;
      data?.subscription?.unsubscribe?.();
    };
  }, []);

  async function refreshStatus() {
    if (!currentUser?.email) {
      setError("No logged-in email found. Please login again.");
      return;
    }

    try {
      setStatusLoading(true);
      const data = await getSubscriptionStatus(currentUser.email);
      setSubscriptionStatus(data);
    } catch (err) {
      setError(err.message || "Could not fetch subscription status");
    } finally {
      setStatusLoading(false);
    }
  }

  async function subscribe(plan) {
    setBusyPlan(plan.id);
    setError("");
    setNotice("");

    if (!currentUser?.email) {
      setError("No logged-in email found. Please login again.");
      setBusyPlan("");
      return;
    }

    try {
      const order = await createSubscriptionOrder({
        plan_id: plan.id,
        customer_name: currentUser.user_metadata?.name || "Gig Worker",
        customer_email: currentUser.email,
      });

      if (order.mode === "mock") {
        await verifySubscriptionPayment({
          razorpay_order_id: order.order_id,
          razorpay_payment_id: `mock_payment_${Date.now()}`,
          razorpay_signature: "mock_signature",
          customer_email: currentUser.email,
          plan_id: plan.id,
        });
        setNotice(
          "Mock subscription activated (Razorpay keys not configured on backend).",
        );
        await refreshStatus();
        return;
      }

      const sdkLoaded = await loadRazorpayScript();
      if (!sdkLoaded) {
        throw new Error("Razorpay SDK failed to load");
      }

      if (!RAZORPAY_KEY_ID) {
        throw new Error("Missing NEXT_PUBLIC_RAZORPAY_KEY_ID in frontend env");
      }

      const rz = new window.Razorpay({
        key: RAZORPAY_KEY_ID,
        amount: order.amount,
        currency: order.currency,
        name: "GigShield",
        description: `${order.plan_name} weekly subscription`,
        order_id: order.order_id,
        prefill: {
          name: currentUser.user_metadata?.name || "Gig Worker",
          email: currentUser.email,
        },
        theme: {
          color: "#0e5a8a",
        },
        handler: async function (response) {
          await verifySubscriptionPayment({
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
            customer_email: currentUser.email,
            plan_id: plan.id,
          });

          setNotice(`Payment verified. ${order.plan_name} subscription is active.`);
          await refreshStatus();
        },
      });

      rz.on("payment.failed", (response) => {
        setError(
          response?.error?.description ||
            "Payment failed. Please retry with test card details.",
        );
      });

      rz.open();
    } catch (err) {
      setError(err.message || "Subscription checkout failed");
    } finally {
      setBusyPlan("");
    }
  }

  return (
    <ProtectedRoute>
      <main className="home-shell">
        <UserTabs />
        <section className="home-hero">
          <p className="kicker">Subscription</p>
          <h1>Manage plan and billing</h1>
          <p>
            Choose a weekly plan and complete checkout through Razorpay.
          </p>
        </section>

        <section className="home-grid">
          {planPreview.map((plan) => (
            <article className="home-card" key={plan.name}>
              <h2>{plan.name}</h2>
              <p>Weekly premium: Rs. {plan.price}</p>
              <button
                type="button"
                onClick={() => subscribe(plan)}
                disabled={busyPlan === plan.id}
              >
                {busyPlan === plan.id ? "Starting checkout..." : "Subscribe"}
              </button>
            </article>
          ))}
        </section>

        <section className="home-card subscription-footer">
          <button type="button" onClick={refreshStatus} disabled={statusLoading}>
            {statusLoading ? "Checking status..." : "Refresh My Subscription"}
          </button>
          <p>
            Logged in as: <strong>{currentUser?.email || "unknown"}</strong>
          </p>
        </section>

        {notice && (
          <section className="home-card">
            <p className="notice">{notice}</p>
          </section>
        )}

        {error && (
          <section className="home-card">
            <p className="error">{error}</p>
          </section>
        )}

        {subscriptionStatus && (
          <section className="home-card">
            <h2>Latest subscription status</h2>
            <p>Status: {subscriptionStatus.latest_status || "none"}</p>
            <p>Plan: {subscriptionStatus.latest_plan_id || "none"}</p>
            <p>Payment ID: {subscriptionStatus.latest_payment_id || "pending"}</p>
          </section>
        )}

        <section className="home-card subscription-footer">
          <p>
            Need detailed plan comparison? Visit the public pricing page.
          </p>
          <Link href="/plans" className="cta-ghost">
            View Plans
          </Link>
        </section>
      </main>
    </ProtectedRoute>
  );
}
