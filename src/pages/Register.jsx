// src/pages/Register.jsx
import { useState } from "react";
import { Link } from "react-router-dom";
import { apiPost } from "../lib/api";
import "../auth.css";

export default function Register() {
  const [email, setEmail]   = useState("");
  const [agency, setAgency] = useState("");
  const [busy, setBusy]     = useState(false);
  const [error, setError]   = useState("");
  const [sent, setSent]     = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await apiPost("/api/send_verification", { email, agency });
      setSent(true);
    } catch (err) {
      if (err.status === 409) {
        setError(
          "This email is already registered. Please log in instead."
        );
      } else if (err.status === 429) {
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
            We sent a sign-in link to <strong>{email}</strong>. Click it to finish
            setting up your account.
          </p>
          <p className="auth-footer">
            Wrong address?{" "}
            <a href="#" onClick={(e) => { e.preventDefault(); setSent(false); }}>
              Try again
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
        <h1 className="auth-title">Register your agency</h1>
        <p className="auth-subtitle">
          Enter your agency email and we'll send you a link to sign in.
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

        <label className="auth-label" htmlFor="agency">Agency name</label>
        <input
          id="agency"
          className="auth-input"
          type="text"
          required
          value={agency}
          onChange={(e) => setAgency(e.target.value)}
          placeholder="e.g. NCPAG"
        />

        <button className="auth-button" type="submit" disabled={busy}>
          {busy ? "Sending link…" : "Send sign-in link"}
        </button>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </form>
    </div>
  );
}