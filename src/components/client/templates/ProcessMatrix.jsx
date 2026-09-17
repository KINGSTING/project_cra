// src/components/client/templates/ProcessMatrix.jsx
import { useEffect, useState } from "react";
import { apiGet, apiPost, apiPatch } from "../../../lib/api";
import "../dashboard.css";

const empty = {
  step_order: 1,
  description: "",
  accountable_officer: "",
  inputs: "",
  outputs: "",
  duration: "",
  remarks: "",
};

export default function ProcessMatrix({ assessmentId }) {
  const [systems, setSystems] = useState([]);
  const [selectedSystem, setSelectedSystem] = useState(null);
  const [steps, setSteps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [modal, setModal] = useState(null);

  // Load critical systems on mount
  useEffect(() => {
    (async () => {
      try {
        const res = await apiGet(`/api/critical_systems?assessment_id=${assessmentId}`);
        setSystems(res.critical_systems);
        if (res.critical_systems.length > 0) {
          setSelectedSystem(res.critical_systems[0].id);
        }
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    })();
  }, [assessmentId]);

  // Load steps when system changes
  useEffect(() => {
    if (!selectedSystem) { setSteps([]); return; }
    (async () => {
      try {
        const res = await apiGet(`/api/process_steps?critical_system_id=${selectedSystem}`);
        setSteps(res.process_steps);
      } catch (err) {
        setError(err.message);
      }
    })();
  }, [selectedSystem]);

  function openCreate() {
    const nextOrder = steps.length > 0
      ? Math.max(...steps.map((s) => s.step_order)) + 1
      : 1;
    setModal({ mode: "create", form: { ...empty, step_order: nextOrder } });
  }

  function openEdit(s) {
    setModal({
      mode: "edit",
      id: s.id,
      form: {
        step_order: s.step_order,
        description: s.description,
        accountable_officer: s.accountable_officer || "",
        inputs: s.inputs || "",
        outputs: s.outputs || "",
        duration: s.duration || "",
        remarks: s.remarks || "",
      },
    });
  }

  async function onSave(e) {
    e.preventDefault();
    setError("");
    const payload = {
      ...modal.form,
      step_order: parseInt(modal.form.step_order, 10),
      critical_system_id: selectedSystem,
    };
    try {
      if (modal.mode === "create") {
        await apiPost("/api/process_steps", payload);
      } else {
        await apiPatch(`/api/process_steps?id=${modal.id}`, payload);
      }
      setModal(null);
      const res = await apiGet(`/api/process_steps?critical_system_id=${selectedSystem}`);
      setSteps(res.process_steps);
    } catch (err) {
      setError(err.message);
    }
  }

  function setField(k, v) {
    setModal((m) => ({ ...m, form: { ...m.form, [k]: v } }));
  }

  if (loading) return <div className="card">Loading…</div>;

  if (systems.length === 0) {
    return (
      <div className="placeholder-panel">
        <h3>No critical systems defined yet</h3>
        <p>Add a critical system in Template 1 before defining process steps.</p>
      </div>
    );
  }

  return (
    <>
      <div className="dash-header" style={{ marginBottom: 16 }}>
        <div>
          <h2 style={{ margin: 0, color: "#0b3d91", fontSize: 20 }}>
            Process Matrix
          </h2>
          <p style={{ margin: "4px 0 0", color: "#6b7280", fontSize: 14 }}>
            Map the step-by-step process for each critical system.
          </p>
        </div>
        <button className="btn btn-primary" onClick={openCreate} disabled={!selectedSystem}>
          + Add step
        </button>
      </div>

      <div className="form-row" style={{ marginBottom: 16, maxWidth: 420 }}>
        <label>Critical System</label>
        <select
          value={selectedSystem || ""}
          onChange={(e) => setSelectedSystem(parseInt(e.target.value, 10))}
        >
          {systems.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {steps.length === 0 && (
        <div className="placeholder-panel">
          <h3>No process steps yet</h3>
          <p>Add steps to describe how this system operates end to end.</p>
        </div>
      )}

      {steps.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: "auto" }}>
          <table className="cs-table">
            <thead>
              <tr>
                <th style={{ width: 50 }}>#</th>
                <th style={{ minWidth: 200 }}>Description</th>
                <th style={{ minWidth: 140 }}>Officer</th>
                <th style={{ minWidth: 140 }}>Inputs</th>
                <th style={{ minWidth: 140 }}>Outputs</th>
                <th style={{ width: 100 }}>Duration</th>
                <th style={{ width: 80 }}></th>
              </tr>
            </thead>
            <tbody>
              {steps.map((s) => (
                <tr key={s.id}>
                  <td style={{ color: "#9ca3af" }}>{s.step_order}</td>
                  <td>
                    <div style={{ fontWeight: 500 }}>{s.description}</div>
                    {s.remarks && (
                      <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>
                        {s.remarks}
                      </div>
                    )}
                  </td>
                  <td>{s.accountable_officer || "—"}</td>
                  <td>{s.inputs || "—"}</td>
                  <td>{s.outputs || "—"}</td>
                  <td>{s.duration || "—"}</td>
                  <td>
                    <div className="row-actions">
                      <button className="icon-btn" onClick={() => openEdit(s)}>Edit</button>
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
            <h2>{modal.mode === "create" ? "Add process step" : "Edit step"}</h2>
            <p>Describe one step in the process flow for this critical system.</p>

            <div className="form-row">
              <label>Step order *</label>
              <input
                type="number" min="1" required
                value={modal.form.step_order}
                onChange={(e) => setField("step_order", e.target.value)}
              />
            </div>

            <div className="form-row">
              <label>Description *</label>
              <textarea
                required maxLength={500}
                value={modal.form.description}
                onChange={(e) => setField("description", e.target.value)}
                placeholder="What happens at this step?"
              />
            </div>

            <div className="form-row">
              <label>Accountable officer / staff</label>
              <input
                type="text"
                value={modal.form.accountable_officer}
                onChange={(e) => setField("accountable_officer", e.target.value)}
              />
            </div>

            <div className="form-row">
              <label>Inputs needed</label>
              <input
                type="text"
                value={modal.form.inputs}
                onChange={(e) => setField("inputs", e.target.value)}
                placeholder="Documents, data, or actions required"
              />
            </div>

            <div className="form-row">
              <label>Outputs</label>
              <input
                type="text"
                value={modal.form.outputs}
                onChange={(e) => setField("outputs", e.target.value)}
                placeholder="Documents or results produced"
              />
            </div>

            <div className="form-row">
              <label>Duration</label>
              <input
                type="text"
                value={modal.form.duration}
                onChange={(e) => setField("duration", e.target.value)}
                placeholder="e.g. 3 days"
              />
            </div>

            <div className="form-row">
              <label>Remarks (gaps, issues, concerns)</label>
              <textarea
                value={modal.form.remarks}
                onChange={(e) => setField("remarks", e.target.value)}
              />
            </div>

            <div className="form-actions">
              <button className="btn btn-primary" type="submit">
                {modal.mode === "create" ? "Add step" : "Save changes"}
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