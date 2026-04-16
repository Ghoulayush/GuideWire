"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  getCurrentSession,
  onAuthStateChange,
  signOutUser,
} from "@/lib/supabase";
import { getSubscriptionStatus } from "@/lib/api";

export default function SiteHeader() {
  const [user, setUser] = useState(null);
  const [name, setName] = useState("");
  const [hasActivePlan, setHasActivePlan] = useState(false);

  async function applyUser(session) {
    const nextUser = session?.user;
    setUser(nextUser || null);

    if (!nextUser) {
      setName("");
      setHasActivePlan(false);
      return;
    }

    const display = nextUser.user_metadata?.name || nextUser.email || "";
    setName(display);

    try {
      const status = await getSubscriptionStatus(nextUser.email || "");
      setHasActivePlan(status?.latest_status === "ACTIVE");
    } catch {
      setHasActivePlan(false);
    }
  }

  useEffect(() => {
    let mounted = true;

    async function bootstrap() {
      const session = await getCurrentSession();
      if (!mounted) return;
      await applyUser(session);
    }

    bootstrap();

    const { data } = onAuthStateChange(async (_event, session) => {
      if (!mounted) return;
      await applyUser(session);
    });

    return () => {
      mounted = false;
      data?.subscription?.unsubscribe?.();
    };
  }, []);

  async function logout() {
    await signOutUser();
    setUser(null);
    setName("");
    setHasActivePlan(false);
    window.location.href = "/auth";
  }

  const navItems = user
    ? hasActivePlan
      ? [
          { href: "/home", label: "Home" },
          { href: "/dashboard", label: "Dashboard" },
          { href: "/simulation", label: "Simulation" },
        ]
      : [
          { href: "/home", label: "Home" },
          { href: "/dashboard", label: "Dashboard" },
          { href: "/plans", label: "Plans" },
        ]
    : [
        { href: "/", label: "About" },
        { href: "/plans", label: "Plans" },
      ];

  return (
    <header className="site-header">
      <Link href="/" className="brand">
        GigShield
      </Link>
      <nav className="nav-row">
        {navItems.map((item) => (
          <Link key={item.href} href={item.href} className="nav-link">
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="user-actions">
        {name ? (
          <>
            <span className="welcome-text">Hi, {name}</span>
            <button type="button" onClick={logout} className="logout-btn">
              Logout
            </button>
          </>
        ) : (
          <Link href="/auth" className="login-link">
            Login
          </Link>
        )}
      </div>
    </header>
  );
}
