"use client";

import { useState } from "react";
import {
  getCurrentUser,
  saveUserProfile,
  signInWithEmail,
  signUpWithEmail,
} from "@/lib/supabase";

const initialState = {
  name: "",
  email: "",
  password: "",
};

export default function AuthPage() {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState(initialState);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  function onChange(event) {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  async function onSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");

    const displayName =
      mode === "signup" ? form.name.trim() : form.email.split("@")[0];

    try {
      const email = form.email.trim();
      const password = form.password;

      const authResult =
        mode === "signup"
          ? await signUpWithEmail(email, password, displayName || "Gig Worker")
          : await signInWithEmail(email, password);

      if (!authResult.ok) {
        throw new Error(authResult.reason || "Authentication failed");
      }

      const user = authResult.data?.user || authResult.data?.session?.user;
      const currentUser = user || (await getCurrentUser());

      if (!currentUser) {
        setNotice(
          "Account created. If email confirmation is enabled, verify email before login.",
        );
        return;
      }

      await saveUserProfile({
        id: currentUser.id,
        email: currentUser.email,
        name: currentUser.user_metadata?.name || displayName || "Gig Worker",
        mode,
      });

      window.location.href = "/home";
    } catch (err) {
      setError(err.message || "Authentication failed");
    } finally {
      setBusy(false);
    }
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
            {busy
              ? "Please wait..."
              : mode === "login"
                ? "Login to Dashboard"
                : "Create Account"}
          </button>
          {error && <p className="error">{error}</p>}
          {notice && <p className="notice">{notice}</p>}
        </form>
      </section>
    </main>
  );
}
