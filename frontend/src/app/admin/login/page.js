"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { loginAdmin } from "@/lib/admin";

export default function AdminLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  function onSubmit(event) {
    event.preventDefault();
    setError("");
    const result = loginAdmin(email, password);
    if (!result.ok) {
      setError(result.message);
      return;
    }
    router.replace("/admin");
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="kicker">Admin Access</p>
        <h1>Admin login</h1>
        <p className="auth-copy">
          Use admin credentials to access users, issues, and subscription
          controls.
        </p>

        <form className="auth-form" onSubmit={onSubmit}>
          <label>
            Admin Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              placeholder="admin@gigshield.local"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              placeholder="admin123"
            />
          </label>
          <button type="submit">Login as Admin</button>
          {error && <p className="error">{error}</p>}
        </form>
      </section>
    </main>
  );
}
