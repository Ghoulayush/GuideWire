"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  getCurrentSession,
  onAuthStateChange,
  signOutUser,
} from "@/lib/supabase";

const navItems = [
  { href: "/", label: "About" },
  { href: "/home", label: "Home" },
  { href: "/plans", label: "Plans" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/admin/login", label: "Admin" },
];

export default function SiteHeader() {
  const [name, setName] = useState("");

  function applyUser(session) {
    const user = session?.user;
    if (!user) {
      setName("");
      return;
    }

    const display = user.user_metadata?.name || user.email || "";
    setName(display);
  }

  useEffect(() => {
    let mounted = true;

    async function bootstrap() {
      const session = await getCurrentSession();
      if (!mounted) return;
      applyUser(session);
    }

    bootstrap();

    const { data } = onAuthStateChange((_event, session) => {
      if (!mounted) return;
      applyUser(session);
    });

    return () => {
      mounted = false;
      data?.subscription?.unsubscribe?.();
    };
  }, []);

  async function logout() {
    await signOutUser();
    setName("");
    window.location.href = "/auth";
  }

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
