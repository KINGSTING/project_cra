// src/pages/Dashboard.jsx
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiGet } from "../../lib/api";
import { useSession } from "../../hooks/useSession";
import "./dashboard.css";

export default function Dashboard() {
  const { session, logout } = useSession();
  const navigate = useNavigate();
  const [assessments, setAssessments] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const res = await apiGet("/api/assessments");
        setAssessments(res.assessments);
      } catch (err) {
        setError(err.message || "Failed to load assessments");
        setAssessments([]);
      }
    })();
  }, []);

  function onLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="dash-shell">
      <div className="dash-topbar">
        <div className="dash-brand">
          IMP-CRA Portal
          <strong>Client Dashboard</strong>
        </div>
        <div className="dash-user">
          <strong>{session.user.email}</strong> · {session.user.agency}
          <button
            onClick={onLogout}
            className="btn btn-secondary"
            style={{ marginLeft: 16, padding: "6px 14px", fontSize: 13 }}
          >
            Sign out
          </button>
        </div>
      </div>

      <div className="dash-container">
        <div className="dash-header">
          <div>
            <h1>Integrity Assessments</h1>
            <p>Manage your agency's IMP cycles and compliance templates.</p>
          </div>
          <Link to="/assessments/new" className="btn btn-primary">
            + New Assessment
          </Link>
        </div>

        {error && <div className="error-banner">{error}</div>}

        {assessments === null && (
          <div className="card"><p>Loading…</p></div>
        )}

        {assessments && assessments.length === 0 && (
          <div className="card empty-state">
            <h2>No assessments yet</h2>
            <p>Start your first IMP compliance cycle to begin.</p>
            <Link to="/assessments/new" className="btn btn-primary">
              Create your first assessment
            </Link>
          </div>
        )}

        {assessments && assessments.length > 0 && (
          <div className="assessment-grid">
            {assessments.map((a) => (
              <Link
                key={a.id}
                to={`/assessments/${a.id}`}
                className="assessment-card"
              >
                <h3>{a.title}</h3>
                <div className="meta">
                  Cycle {a.cycle_year} · Updated{" "}
                  {new Date(a.updated_at).toLocaleDateString()}
                </div>
                <span className={`status-pill status-${a.status}`}>
                  {a.status.replace("_", " ")}
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}