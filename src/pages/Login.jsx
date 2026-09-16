// src/pages/Login.jsx
import { useState } from "react";
import { Link } from "react-router-dom";
import { apiPost } from "../lib/api";
import "../auth.css";

export default function Login() {
  const [email, setEmail] = useState("");
  const [busy, setBusy]   = useState(false);
  const [error, setError] = useState("");
  const [sent, setSent]   = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await apiPost("/api/request_link", { email });
      setSent(true);
    } catch (err) {
      if (err.status === 429) {
        setError(
          `Please wait ${err.payload?.retry_after ?? 60}s before requesting another link.`
        );
      } else {
        setError(err.message || "Something went wrong. Please try again.");
      }
    } finally {
      setBusy(false);
    }
  }

  if (sent) {
    return (
      <div className="auth-shell">
        <div className="auth-card">
          <div className="auth-brand">IMP-CRA Portal</div>
          <h1 className="auth-title">Check your email</h1>
          <p className="auth-subtitle">
            If <strong>{email}</strong> is registered, we sent a sign-in link to it.
          </p>
          <p className="auth-footer">
            <a href="#" onClick={(e) => { e.preventDefault(); setSent(false); }}>
              Use a different email
            </a>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-shell">
      <form className="auth-card" onSubmit={onSubmit}>
        <div className="auth-brand">IMP-CRA Portal</div>
        <h1 className="auth-title">Sign in</h1>
        <p className="auth-subtitle">
          Enter your email and we'll send you a sign-in link.
        </p>

        {error && <div className="auth-error">{error}</div>}

        <label className="auth-label" htmlFor="email">Email address</label>
        <input
          id="email"
          className="auth-input"
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@agency.gov.ph"
        />

        <button className="auth-button" type="submit" disabled={busy}>
          {busy ? "Sending link…" : "Send sign-in link"}
        </button>

        <p className="auth-footer">
          New here? <Link to="/register">Register your agency</Link>
        </p>
      </form>
    </div>
  );
}