// src/pages/CreateAssessment.jsx
import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { apiPost } from "../../lib/api";
import { useSession } from "../../hooks/useSession";
import "./dashboard.css";

export default function CreateAssessment() {
  const { session } = useSession();
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [year, setYear] = useState(new Date().getFullYear());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const res = await apiPost("/api/assessments", {
        title,
        cycle_year: parseInt(year, 10),
      });
      navigate(`/assessments/${res.assessment.id}`, { replace: true });
    } catch (err) {
      setError(err.message || "Could not create assessment");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="dash-shell">
      <div className="dash-topbar">
        <div className="dash-brand">
          IMP-CRA Portal
          <strong>New Assessment</strong>
        </div>
        <div className="dash-user">
          <strong>{session.user.email}</strong> · {session.user.agency}
        </div>
      </div>

      <div className="dash-container" style={{ maxWidth: 640 }}>
        <div className="dash-header">
          <div>
            <h1>Start a new IMP cycle</h1>
            <p>
              Name your assessment and choose the cycle year. You can change
              these later.
            </p>
          </div>
        </div>

        {error && <div className="error-banner">{error}</div>}

        <form className="card" onSubmit={onSubmit}>
          <div className="form-row">
            <label htmlFor="title">Assessment title</label>
            <input
              id="title"
              type="text"
              required
              maxLength={200}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. NCPAG IMP Cycle 2026"
            />
          </div>

          <div className="form-row">
            <label htmlFor="year">Cycle year</label>
            <input
              id="year"
              type="number"
              required
              min="2000"
              max="2100"
              value={year}
              onChange={(e) => setYear(e.target.value)}
            />
          </div>

          <div className="form-actions">
            <button className="btn btn-primary" type="submit" disabled={busy}>
              {busy ? "Creating…" : "Create assessment"}
            </button>
            <Link to="/dashboard" className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}