// src/pages/AssessmentDetail.jsx
import { useEffect, useState } from "react";
import { useParams, Link, useNavigate, useSearchParams } from "react-router-dom";
import { apiGet, apiDelete } from "../../lib/api";
import { useSession } from "../../hooks/useSession";
import CriticalSystems from "./templates/CriticalSystems";
import ProcessMatrix from "./templates/ProcessMatrix";
import RiskRegister from "./templates/RiskRegister";
import AssessmentReport from "./templates/AssessmentReport";
import "./dashboard.css";
const TEMPLATES = [
  { key: "systems",  label: "Template 1 · Critical Systems" },
  { key: "matrix",   label: "Template 2 · Process Matrix" },
  { key: "risks",    label: "Template 3 · Risk Register" },
  { key: "report",   label: "Template 4 · Assessment Report" },
];

export default function AssessmentDetail() {
  const { id } = useParams();
  const { session } = useSession();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const active = params.get("tab") || "systems";

  const [assessment, setAssessment] = useState(null);
  const [error, setError] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiGet(`/api/assessments?id=${id}`);
        setAssessment(res.assessment);
      } catch (err) {
        setError(
          err.status === 404
            ? "Assessment not found or you don't have access."
            : err.message
        );
      }
    })();
  }, [id]);

  async function onDelete() {
    try {
      await apiDelete(`/api/assessments?id=${id}`);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.message);
      setConfirmDelete(false);
    }
  }

  function setTab(key) {
    setParams({ tab: key });
  }

  if (error) {
    return (
      <div className="dash-shell">
        <div className="dash-topbar">
          <div className="dash-brand">
            IMP-CRA Portal
            <strong>Assessment</strong>
          </div>
        </div>
        <div className="dash-container">
          <div className="error-banner">{error}</div>
          <Link to="/dashboard" className="btn btn-secondary">← Back to dashboard</Link>
        </div>
      </div>
    );
  }

  if (!assessment) {
    return (
      <div className="dash-shell">
        <div className="dash-topbar">
          <div className="dash-brand">
            IMP-CRA Portal
            <strong>Loading…</strong>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dash-shell">
      <div className="dash-topbar">
        <div className="dash-brand">
          IMP-CRA Portal
          <strong>{assessment.title}</strong>
        </div>
        <div className="dash-user">
          <strong>{session.user.email}</strong> · {session.user.agency}
        </div>
      </div>

      <div className="dash-container">
        <div className="dash-header">
          <div>
            <h1>{assessment.title}</h1>
            <p>
              Cycle {assessment.cycle_year} ·{" "}
              <span className={`status-pill status-${assessment.status}`}>
                {assessment.status.replace("_", " ")}
              </span>
            </p>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <Link to="/dashboard" className="btn btn-secondary">← Dashboard</Link>
          </div>
        </div>

        <div className="template-tabs">
          {TEMPLATES.map((t) => (
            <button
              key={t.key}
              className={`template-tab ${active === t.key ? "active" : ""}`}
              onClick={() => setTab(t.key)}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div>
          {active === "systems" && <CriticalSystems assessmentId={assessment.id} />}
          {active === "matrix"  && <ProcessMatrix   assessmentId={assessment.id} />}
          {active === "risks"   && <RiskRegister    assessmentId={assessment.id} />}
          {active === "report"  && <AssessmentReport assessmentId={assessment.id} />}
        </div>
      </div>

      {confirmDelete && (
        <div className="modal-backdrop" onClick={() => setConfirmDelete(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Delete this assessment?</h2>
            <p>
              This will permanently remove the assessment and all its critical
              systems, process steps, and risk entries. This cannot be undone.
            </p>
            <div className="form-actions">
              <button className="btn btn-danger" onClick={onDelete}>
                Yes, delete permanently
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => setConfirmDelete(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}