"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { clearStoredUser, getStoredUser } from "@/lib/auth";

const navItems = [
  { href: "/", label: "About" },
  { href: "/plans", label: "Plans" },
  { href: "/dashboard", label: "Dashboard" },
];

export default function SiteHeader() {
  const [name, setName] = useState("");

  useEffect(() => {
    const syncName = () => {
      const current = getStoredUser();
      setName(current?.name || "");
    };

    const frameId = window.requestAnimationFrame(syncName);
    window.addEventListener("storage", syncName);

    return () => {
      window.cancelAnimationFrame(frameId);
      window.removeEventListener("storage", syncName);
    };
  }, []);

  function logout() {
    clearStoredUser();
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
