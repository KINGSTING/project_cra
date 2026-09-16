// src/pages/Dashboard.jsx
import { useSession } from "../hooks/useSession";
import { useNavigate } from "react-router-dom";

export default function Dashboard() {
  const { session, logout } = useSession();
  const navigate = useNavigate();

  function onLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div style={{
      minHeight: "100vh",
      background: "#f4f6f8",
      padding: "48px 24px",
      fontFamily: '-apple-system, "Segoe UI", Roboto, sans-serif',
    }}>
      <div style={{ maxWidth: 720, margin: "0 auto" }}>
        <div style={{
          fontSize: 12,
          letterSpacing: 1.5,
          textTransform: "uppercase",
          color: "#6b7280",
          marginBottom: 4,
        }}>
          IMP-CRA Portal
        </div>
        <h1 style={{ margin: "0 0 8px", color: "#0b3d91" }}>
          Welcome, {session.user.email}
        </h1>
        <p style={{ color: "#6b7280", marginBottom: 32 }}>
          Agency: <strong>{session.user.agency}</strong> · Role: <strong>{session.user.role}</strong>
        </p>

        <div style={{
          background: "#fff",
          borderRadius: 10,
          padding: 24,
          boxShadow: "0 4px 20px rgba(0,0,0,0.04)",
        }}>
          <h2 style={{ marginTop: 0 }}>Client Dashboard</h2>
          <p style={{ color: "#6b7280", marginBottom: 0 }}>
            Phase 4 goes here. You're authenticated — the session is working end to end.
          </p>
        </div>

        <button
          onClick={onLogout}
          style={{
            marginTop: 24,
            background: "transparent",
            border: "1px solid #d1d5db",
            borderRadius: 6,
            padding: "8px 16px",
            cursor: "pointer",
            color: "#374151",
          }}
        >
          Sign out
        </button>
      </div>
    </div>
  );
}