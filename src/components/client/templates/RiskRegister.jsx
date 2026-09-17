// src/components/client/templates/RiskRegister.jsx
import { useEffect, useState } from "react";
import { apiGet, apiPost, apiPatch } from "../../../lib/api";
import "../dashboard.css";

const DIMENSIONS = [
  { value: "service_delivery",                label: "Service Delivery" },
  { value: "institutional_leadership",        label: "Institutional Leadership" },
  { value: "financial_procurement_asset",     label: "Financial, Procurement & Asset Mgmt" },
  { value: "human_resource",                  label: "Human Resource Mgmt & Dev" },
  { value: "corruption_risk_mgmt",            label: "Corruption Risk Management" },
  { value: "internal_reporting_investigation",label: "Internal Reporting & Investigation" },
];

const empty = {
  corruption_risk: "",
  corruption_scheme: "",
  probability: 5,
  impact: 5,
  mitigating_control: "",
  control_rating: "M",
  residual_risk: "",
  integrity_measure: "",
  dimension: "",
};

function band(score) {
  if (score >= 11) return "H";
  if (score >= 6)  return "M";
  return "L";
}

function computePreview(form) {
  const p = parseInt(form.probability, 10);
  const i = parseInt(form.impact, 10);
  if (!p || !i) return { inherent: null, inBand: null, resBand: null };
  const inherent = (p + i) / 2;
  const inBand = band(inherent);
  const order = ["L", "M", "H"];
  let idx = order.indexOf(inBand);
  if (form.control_rating === "H") idx = Math.max(0, idx - 1);
  else if (form.control_rating === "L") idx = Math.min(2, idx + 1);
  return { inherent, inBand, resBand: order[idx] };
}

function BandPill({ value }) {
  if (!value) return <span style={{ color: "#9ca3af" }}>—</span>;
  const cls = value === "H" ? "check-no" : value === "M" ? "status-under_review" : "check-yes";
  return <span className={`check-icon ${cls}`}>{value}</span>;
}

export default function RiskRegister({ assessmentId }) {
  const [systems, setSystems] = useState([]);
  const [selectedSystem, setSelectedSystem] = useState(null);
  const [steps, setSteps] = useState([]);
  const [selectedStep, setSelectedStep] = useState(null);
  const [risks, setRisks] = useState([]);
  const [error, setError] = useState("");
  const [modal, setModal] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load systems
  useEffect(() => {
    (async () => {
      try {
        const res = await apiGet(`/api/critical_systems?assessment_id=${assessmentId}`);
        setSystems(res.critical_systems);
        if (res.critical_systems.length > 0) setSelectedSystem(res.critical_systems[0].id);
        setLoading(false);
      } catch (err) { setError(err.message); setLoading(false); }
    })();
  }, [assessmentId]);

  // Load steps when system changes
  useEffect(() => {
    if (!selectedSystem) { setSteps([]); setSelectedStep(null); return; }
    (async () => {
      try {
        const res = await apiGet(`/api/process_steps?critical_system_id=${selectedSystem}`);
        setSteps(res.process_steps);
        setSelectedStep(res.process_steps[0]?.id ?? null);
      } catch (err) { setError(err.message); }
    })();
  }, [selectedSystem]);

  // Load risks when step changes
  useEffect(() => {
    if (!selectedStep) { setRisks([]); return; }
    (async () => {
      try {
        const res = await apiGet(`/api/corruption_risks?process_step_id=${selectedStep}`);
        setRisks(res.corruption_risks);
      } catch (err) { setError(err.message); }
    })();
  }, [selectedStep]);

  async function reloadRisks() {
    if (!selectedStep) return;
    const res = await apiGet(`/api/corruption_risks?process_step_id=${selectedStep}`);
    setRisks(res.corruption_risks);
  }

  function openCreate() {
    setModal({ mode: "create", form: { ...empty } });
  }

  function openEdit(r) {
    setModal({
      mode: "edit",
      id: r.id,
      form: {
        corruption_risk: r.corruption_risk || "",
        corruption_scheme: r.corruption_scheme || "",
        probability: r.probability ?? 5,
        impact: r.impact ?? 5,
        mitigating_control: r.mitigating_control || "",
        control_rating: r.control_rating || "M",
        residual_risk: r.residual_risk || "",
        integrity_measure: r.integrity_measure || "",
        dimension: r.dimension || "",
      },
    });
  }

  async function onSave(e) {
    e.preventDefault();
    setError("");
    const payload = {
      ...modal.form,
      probability: parseInt(modal.form.probability, 10),
      impact: parseInt(modal.form.impact, 10),
      process_step_id: selectedStep,
    };
    try {
      if (modal.mode === "create") {
        await apiPost("/api/corruption_risks", payload);
      } else {
        await apiPatch(`/api/corruption_risks?id=${modal.id}`, payload);
      }
      setModal(null);
      reloadRisks();
    } catch (err) { setError(err.message); }
  }

  function setField(k, v) {
    setModal((m) => ({ ...m, form: { ...m.form, [k]: v } }));
  }

  if (loading) return <div className="card">Loading…</div>;

  if (systems.length === 0) {
    return (
      <div className="placeholder-panel">
        <h3>No critical systems defined</h3>
        <p>Complete Template 1 first.</p>
      </div>
    );
  }

  return (
    <>
      <div className="dash-header" style={{ marginBottom: 16 }}>
        <div>
          <h2 style={{ margin: 0, color: "#0b3d91", fontSize: 20 }}>
            Corruption Risk Register
          </h2>
          <p style={{ margin: "4px 0 0", color: "#6b7280", fontSize: 14 }}>
            Score each risk. Inherent risk = (probability + impact) / 2.
          </p>
        </div>
        <button className="btn btn-primary" onClick={openCreate} disabled={!selectedStep}>
          + Add risk
        </button>
      </div>

      <div style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
        <div className="form-row" style={{ flex: "1 1 260px", margin: 0 }}>
          <label>Critical System</label>
          <select value={selectedSystem || ""} onChange={(e) => setSelectedSystem(parseInt(e.target.value, 10))}>
            {systems.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </div>
        <div className="form-row" style={{ flex: "1 1 260px", margin: 0 }}>
          <label>Process Step</label>
          <select value={selectedStep || ""} onChange={(e) => setSelectedStep(parseInt(e.target.value, 10))}>
            {steps.length === 0 && <option value="">No steps defined</option>}
            {steps.map((s) => (
              <option key={s.id} value={s.id}>
                Step {s.step_order}: {s.description.slice(0, 60)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {!selectedStep && (
        <div className="placeholder-panel">
          <h3>No process step selected</h3>
          <p>Add a process step in Template 2 first.</p>
        </div>
      )}

      {selectedStep && risks.length === 0 && (
        <div className="placeholder-panel">
          <h3>No risks recorded for this step</h3>
          <p>Add the first corruption risk to begin scoring.</p>
        </div>
      )}

      {selectedStep && risks.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: "auto" }}>
          <table className="cs-table">
            <thead>
              <tr>
                <th style={{ minWidth: 200 }}>Corruption Risk</th>
                <th style={{ width: 90, textAlign: "center" }}>P</th>
                <th style={{ width: 90, textAlign: "center" }}>I</th>
                <th style={{ width: 110, textAlign: "center" }}>Inherent</th>
                <th style={{ width: 110, textAlign: "center" }}>Control</th>
                <th style={{ width: 110, textAlign: "center" }}>Residual</th>
                <th style={{ width: 80 }}></th>
              </tr>
            </thead>
            <tbody>
              {risks.map((r) => (
                <tr key={r.id}>
                  <td>
                    <div style={{ fontWeight: 500 }}>{r.corruption_risk}</div>
                    {r.corruption_scheme && (
                      <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>
                        {r.corruption_scheme}
                      </div>
                    )}
                  </td>
                  <td style={{ textAlign: "center" }}>{r.probability ?? "—"}</td>
                  <td style={{ textAlign: "center" }}>{r.impact ?? "—"}</td>
                  <td style={{ textAlign: "center" }}>
                    <BandPill value={r.inherent_band} />
                    <div style={{ fontSize: 11, color: "#6b7280", marginTop: 2 }}>
                      {r.inherent_risk ?? "—"}
                    </div>
                  </td>
                  <td style={{ textAlign: "center" }}>{r.control_rating || "—"}</td>
                  <td style={{ textAlign: "center" }}>
                    <BandPill value={r.residual_band} />
                  </td>
                  <td>
                    <div className="row-actions">
                      <button className="icon-btn" onClick={() => openEdit(r)}>Edit</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modal && (
        <div className="modal-backdrop" onClick={() => setModal(null)}>
          <form className="modal" onSubmit={onSave} onClick={(e) => e.stopPropagation()}>
            <h2>{modal.mode === "create" ? "Add corruption risk" : "Edit risk"}</h2>

            <div className="form-row">
              <label>Corruption risk *</label>
              <input
                type="text" required maxLength={500}
                value={modal.form.corruption_risk}
                onChange={(e) => setField("corruption_risk", e.target.value)}
                placeholder="e.g. Collusion with supplier"
              />
            </div>

            <div className="form-row">
              <label>Corruption scheme (how it could occur)</label>
              <textarea
                value={modal.form.corruption_scheme}
                onChange={(e) => setField("corruption_scheme", e.target.value)}
              />
            </div>

            <div style={{ display: "flex", gap: 12 }}>
              <div className="form-row" style={{ flex: 1 }}>
                <label>Probability (1–15)</label>
                <input
                  type="number" min="1" max="15" required
                  value={modal.form.probability}
                  onChange={(e) => setField("probability", e.target.value)}
                />
              </div>
              <div className="form-row" style={{ flex: 1 }}>
                <label>Impact (1–15)</label>
                <input
                  type="number" min="1" max="15" required
                  value={modal.form.impact}
                  onChange={(e) => setField("impact", e.target.value)}
                />
              </div>
            </div>

            {/* Live-computed preview */}
            {(() => {
              const { inherent, inBand, resBand } = computePreview(modal.form);
              if (inherent === null) return null;
              return (
                <div style={{
                  background: "#f9fafb", padding: 12, borderRadius: 6,
                  marginBottom: 16, fontSize: 13,
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ color: "#6b7280" }}>Computed inherent risk</span>
                    <strong>{inherent} — Band {inBand}</strong>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#6b7280" }}>Projected residual band</span>
                    <strong>{resBand}</strong>
                  </div>
                </div>
              );
            })()}

            <div className="form-row">
              <label>Mitigating control (existing)</label>
              <textarea
                value={modal.form.mitigating_control}
                onChange={(e) => setField("mitigating_control", e.target.value)}
              />
            </div>

            <div className="form-row">
              <label>Control effectiveness</label>
              <select
                value={modal.form.control_rating}
                onChange={(e) => setField("control_rating", e.target.value)}
              >
                <option value="H">High — effective</option>
                <option value="M">Medium — partially effective</option>
                <option value="L">Low — ineffective</option>
              </select>
            </div>

            <div className="form-row">
              <label>Residual risk (description)</label>
              <textarea
                value={modal.form.residual_risk}
                onChange={(e) => setField("residual_risk", e.target.value)}
              />
            </div>

            <div className="form-row">
              <label>Proposed integrity measure</label>
              <textarea
                value={modal.form.integrity_measure}
                onChange={(e) => setField("integrity_measure", e.target.value)}
              />
            </div>

            <div className="form-row">
              <label>IMP Dimension</label>
              <select
                value={modal.form.dimension}
                onChange={(e) => setField("dimension", e.target.value)}
              >
                <option value="">— Select a dimension —</option>
                {DIMENSIONS.map((d) => (
                  <option key={d.value} value={d.value}>{d.label}</option>
                ))}
              </select>
            </div>

            <div className="form-actions">
              <button className="btn btn-primary" type="submit">
                {modal.mode === "create" ? "Add risk" : "Save changes"}
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => setModal(null)}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}