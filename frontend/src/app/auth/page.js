"use client";

import { useState } from "react";
import { setStoredUser } from "@/lib/auth";

const initialState = {
  name: "",
  email: "",
  password: "",
};

export default function AuthPage() {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState(initialState);

  function onChange(event) {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  function onSubmit(event) {
    event.preventDefault();

    const displayName =
      mode === "signup" ? form.name.trim() : form.email.split("@")[0];

    setStoredUser({
      name: displayName || "Gig Worker",
      email: form.email.trim(),
      mode,
    });

    window.location.href = "/dashboard";
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="kicker">Account Access</p>
        <h1>{mode === "login" ? "Welcome back" : "Create your account"}</h1>
        <p className="auth-copy">
          Use login to continue to your dashboard, or sign up to create a new
          workspace identity.
        </p>

        <div className="auth-switch">
          <button
            type="button"
            className={mode === "login" ? "switch-active" : "switch-idle"}
            onClick={() => setMode("login")}
          >
            Login
          </button>
          <button
            type="button"
            className={mode === "signup" ? "switch-active" : "switch-idle"}
            onClick={() => setMode("signup")}
          >
            Sign Up
          </button>
        </div>

        <form className="auth-form" onSubmit={onSubmit}>
          {mode === "signup" && (
            <label>
              Full Name
              <input
                name="name"
                value={form.name}
                onChange={onChange}
                required
                placeholder="Ravi Kumar"
              />
            </label>
          )}
          <label>
            Email
            <input
              name="email"
              type="email"
              value={form.email}
              onChange={onChange}
              required
              placeholder="ravi@sample.com"
            />
          </label>
          <label>
            Password
            <input
              name="password"
              type="password"
              value={form.password}
              onChange={onChange}
              required
              minLength={6}
              placeholder="Minimum 6 characters"
            />
          </label>
          <button type="submit">
            {mode === "login" ? "Login to Dashboard" : "Create Account"}
          </button>
        </form>
      </section>
    </main>
  );
}
