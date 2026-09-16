import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { apiPost } from "../lib/api";
import { useSession } from "../hooks/useSession";
import "../auth.css";

export default function Verify() {
  const [params]         = useSearchParams();
  const navigate         = useNavigate();
  const { login }        = useSession();
  const [state, setState] = useState("verifying");
  const [error, setError] = useState("");
  const firedRef = useRef(false);

  useEffect(() => {
    if (firedRef.current) return;
    firedRef.current = true;

    const token = params.get("token");
    if (!token) {
      setState("error");
      setError("Missing token. Please use the link from your email.");
      return;
    }

    (async () => {
      try {
        const res = await apiPost("/api/verify_email", { token });
        login(res.token);
        navigate("/dashboard", { replace: true });
      } catch (err) {
        setState("error");
        setError(friendlyError(err));
      }
    })();
  }, [params, login, navigate]);

  function friendlyError(err) {
    const code = err.payload?.error || err.message;
    switch (code) {
      case "invalid_token":  return "This link is invalid. Please request a new one.";
      case "already_used":   return "This link has already been used. Request a new one below.";
      case "expired":        return "This link has expired. Request a new one below.";
      case "missing_token":  return "Missing token. Please use the link from your email.";
      default:               return "We couldn't verify this link. Please try again.";
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-brand">IMP-CRA Portal</div>

        {state === "verifying" && (
          <>
            <h1 className="auth-title">Signing you in…</h1>
            <p className="auth-subtitle">Please wait a moment.</p>
          </>
        )}

        {state === "error" && (
          <>
            <h1 className="auth-title">Sign-in failed</h1>
            <div className="auth-error">{error}</div>
            <p className="auth-footer">
              <Link to="/login">Request a new sign-in link</Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}