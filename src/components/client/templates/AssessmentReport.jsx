// src/components/client/templates/AssessmentReport.jsx
import { useEffect, useState } from "react";
import { apiGet } from "../../../lib/api";
import "../dashboard.css";

const DIM_LABELS = {
  service_delivery: "Service Delivery",
  institutional_leadership: "Institutional Leadership",
  financial_procurement_asset: "Financial, Procurement & Asset Mgmt",
  human_resource: "Human Resource Mgmt & Dev",
  corruption_risk_mgmt: "Corruption Risk Management",
  internal_reporting_investigation: "Internal Reporting & Investigation",
};

function BandPill({ value }) {
  if (!value) return <span style={{ color: "#9ca3af" }}>—</span>;
  const cls = value === "H" ? "check-no" : value === "M" ? "status-under_review" : "check-yes";
  return <span className={`check-icon ${cls}`}>{value}</span>;
}

export default function AssessmentReport({ assessmentId }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const res = await apiGet(`/api/assessment_report?assessment_id=${assessmentId}`);
        setData(res);
      } catch (err) { setError(err.message); }
    })();
  }, [assessmentId]);

  if (error) return <div className="error-banner">{error}</div>;
  if (!data) return <div className="card">Loading report…</div>;

  const { assessment, critical_systems } = data;
  const totalSystems = critical_systems.length;
  const totalSteps = critical_systems.reduce((n, s) => n + s.process_steps.length, 0);
  const totalRisks = critical_systems.reduce(
    (n, s) => n + s.process_steps.reduce((m, st) => m + st.corruption_risks.length, 0),
    0,
  );

  return (
    <>
      <div className="dash-header" style={{ marginBottom: 16 }}>
        <div>
          <h2 style={{ margin: 0, color: "#0b3d91", fontSize: 20 }}>
            Assessment Report
          </h2>
          <p style={{ margin: "4px 0 0", color: "#6b7280", fontSize: 14 }}>
            Read-only summary of your full assessment. Use Print to save as PDF.
          </p>
        </div>
        <button className="btn btn-secondary" onClick={() => window.print()}>
          Print / Save as PDF
        </button>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <h3 style={{ marginTop: 0, color: "#0b3d91" }}>{assessment.title}</h3>
        <div style={{ color: "#6b7280", fontSize: 14, marginBottom: 16 }}>
          Agency: <strong>{assessment.agency}</strong> · Cycle {assessment.cycle_year} ·{" "}
          <span className={`status-pill status-${assessment.status}`}>
            {assessment.status.replace("_", " ")}
          </span>
        </div>
        <div style={{ display: "flex", gap: 24, fontSize: 13, color: "#374151" }}>
          <div><strong>{totalSystems}</strong> critical system(s)</div>
          <div><strong>{totalSteps}</strong> process step(s)</div>
          <div><strong>{totalRisks}</strong> corruption risk(s)</div>
        </div>
      </div>

      {critical_systems.length === 0 && (
        <div className="placeholder-panel">
          <h3>Nothing to report yet</h3>
          <p>Start with Template 1 to define critical systems.</p>
        </div>
      )}

      {critical_systems.map((sys) => (
        <div key={sys.id} className="card" style={{ marginBottom: 20 }}>
          <h3 style={{ marginTop: 0, color: "#0b3d91", fontSize: 17 }}>
            {sys.ranking ? `${sys.ranking}. ` : ""}{sys.name}
          </h3>
          {sys.description && (
            <p style={{ color: "#6b7280", fontSize: 14, marginTop: 4 }}>{sys.description}</p>
          )}

          <div style={{ margin: "12px 0 20px", fontSize: 12, color: "#6b7280" }}>
            Criteria:{" "}
            {sys.high_impact && <strong style={{ color: "#065f46" }}>High Impact · </strong>}
            {sys.high_developmental && <strong style={{ color: "#065f46" }}>High Dev · </strong>}
            {sys.pro_poor && <strong style={{ color: "#065f46" }}>Pro-Poor</strong>}
            {!sys.high_impact && !sys.high_developmental && !sys.pro_poor && "none"}
          </div>

          {sys.process_steps.length === 0 && (
            <p style={{ color: "#9ca3af", fontStyle: "italic" }}>No process steps defined.</p>
          )}

          {sys.process_steps.map((step) => (
            <div key={step.id} style={{
              marginBottom: 16, paddingLeft: 16,
              borderLeft: "3px solid #e5e7eb",
            }}>
              <div style={{ fontWeight: 600, fontSize: 14 }}>
                Step {step.step_order}: {step.description}
              </div>
              <div style={{ fontSize: 12, color: "#6b7280", marginTop: 4 }}>
                {step.accountable_officer && <span>Officer: {step.accountable_officer} · </span>}
                {step.duration && <span>Duration: {step.duration}</span>}
              </div>

              {step.corruption_risks.length > 0 && (
                <table className="cs-table" style={{ marginTop: 10 }}>
                  <thead>
                    <tr>
                      <th>Corruption Risk</th>
                      <th style={{ width: 60, textAlign: "center" }}>P</th>
                      <th style={{ width: 60, textAlign: "center" }}>I</th>
                      <th style={{ width: 90, textAlign: "center" }}>Inherent</th>
                      <th style={{ width: 90, textAlign: "center" }}>Residual</th>
                      <th style={{ width: 220 }}>Dimension</th>
                    </tr>
                  </thead>
                  <tbody>
                    {step.corruption_risks.map((r) => (
                      <tr key={r.id}>
                        <td>
                          <div style={{ fontWeight: 500 }}>{r.corruption_risk}</div>
                          {r.integrity_measure && (
                            <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>
                              Measure: {r.integrity_measure}
                            </div>
                          )}
                        </td>
                        <td style={{ textAlign: "center" }}>{r.probability}</td>
                        <td style={{ textAlign: "center" }}>{r.impact}</td>
                        <td style={{ textAlign: "center" }}>
                          <BandPill value={r.inherent_band} />
                          <div style={{ fontSize: 11, color: "#6b7280" }}>{r.inherent_risk}</div>
                        </td>
                        <td style={{ textAlign: "center" }}>
                          <BandPill value={r.residual_band} />
                        </td>
                        <td style={{ fontSize: 12, color: "#6b7280" }}>
                          {DIM_LABELS[r.dimension] || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {step.corruption_risks.length === 0 && (
                <p style={{ color: "#9ca3af", fontStyle: "italic", fontSize: 13, marginTop: 6 }}>
                  No risks recorded.
                </p>
              )}
            </div>
          ))}
        </div>
      ))}
    </>
  );
}