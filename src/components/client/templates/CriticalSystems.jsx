// src/pages/templates/CriticalSystems.jsx
import { useEffect, useState } from "react";
import { apiGet, apiPost, apiPatch, apiDelete } from "../../../lib/api";
import "../dashboard.css";

const empty = {
  name: "",
  description: "",
  high_impact: false,
  high_developmental: false,
  pro_poor: false,
  ranking: "",
};

export default function CriticalSystems({ assessmentId }) {
  const [systems, setSystems] = useState(null);
  const [error, setError] = useState("");
  const [modal, setModal] = useState(null); // null | { mode: "create" | "edit", form: {...}, id? }

  async function load() {
    try {
      const res = await apiGet(`/api/critical_systems?assessment_id=${assessmentId}`);
      setSystems(res.critical_systems);
    } catch (err) {
      setError(err.message);
      setSystems([]);
    }
  }

  useEffect(() => { load(); }, [assessmentId]);

  function openCreate() {
    setModal({ mode: "create", form: { ...empty } });
  }
  function openEdit(s) {
    setModal({
      mode: "edit",
      id: s.id,
      form: {
        name: s.name,
        description: s.description || "",
        high_impact: s.high_impact,
        high_developmental: s.high_developmental,
        pro_poor: s.pro_poor,
        ranking: s.ranking ?? "",
      },
    });
  }

  async function onSave(e) {
    e.preventDefault();
    setError("");
    const payload = {
      ...modal.form,
      ranking: modal.form.ranking === "" ? null : parseInt(modal.form.ranking, 10),
      assessment_id: assessmentId,
    };
    try {
      if (modal.mode === "create") {
        await apiPost("/api/critical_systems", payload);
      } else {
        await apiPatch(`/api/critical_systems?id=${modal.id}`, payload);
      }
      setModal(null);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function onDelete(id) {
    if (!confirm("Delete this critical system and its process steps?")) return;
    try {
      await apiDelete(`/api/critical_systems?id=${id}`);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  function setField(k, v) {
    setModal((m) => ({ ...m, form: { ...m.form, [k]: v } }));
  }

  return (
    <>
      <div className="dash-header" style={{ marginBottom: 16 }}>
        <div>
          <h2 style={{ margin: 0, color: "#0b3d91", fontSize: 20 }}>
            Critical Systems for Assessment
          </h2>
          <p style={{ margin: "4px 0 0", color: "#6b7280", fontSize: 14 }}>
            Identify the operation systems in your agency with the highest impact,
            developmental significance, and pro-poor orientation.
          </p>
        </div>
        <button className="btn btn-primary" onClick={openCreate}>
          + Add system
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {systems === null && <div className="card">Loading…</div>}

      {systems && systems.length === 0 && (
        <div className="placeholder-panel">
          <h3>No critical systems yet</h3>
          <p>Add your first critical system to begin the assessment.</p>
        </div>
      )}

      {systems && systems.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table className="cs-table">
            <thead>
              <tr>
                <th style={{ width: 40 }}>#</th>
                <th>System Name</th>
                <th style={{ width: 90, textAlign: "center" }}>High Impact</th>
                <th style={{ width: 90, textAlign: "center" }}>High Dev.</th>
                <th style={{ width: 90, textAlign: "center" }}>Pro-Poor</th>
                <th style={{ width: 70, textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {systems.map((s) => (
                <tr key={s.id}>
                  <td style={{ color: "#9ca3af" }}>{s.ranking ?? "—"}</td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{s.name}</div>
                    {s.description && (
                      <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>
                        {s.description}
                      </div>
                    )}
                  </td>
                  <td style={{ textAlign: "center" }}>
                    <Check on={s.high_impact} />
                  </td>
                  <td style={{ textAlign: "center" }}>
                    <Check on={s.high_developmental} />
                  </td>
                  <td style={{ textAlign: "center" }}>
                    <Check on={s.pro_poor} />
                  </td>
                  <td>
                    <div className="row-actions">
                    <button className="icon-btn" onClick={() => openEdit(s)}>
                        Edit
                    </button>
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
            <h2>{modal.mode === "create" ? "Add critical system" : "Edit system"}</h2>
            <p>
              Describe one operation system that will be assessed for corruption
              vulnerabilities.
            </p>

            <div className="form-row">
              <label>System name *</label>
              <input
                type="text"
                required
                maxLength={200}
                value={modal.form.name}
                onChange={(e) => setField("name", e.target.value)}
                placeholder="e.g. Procurement of Goods and Services"
              />
            </div>

            <div className="form-row">
              <label>Description</label>
              <textarea
                value={modal.form.description}
                onChange={(e) => setField("description", e.target.value)}
                placeholder="Brief scope and purpose of this system"
              />
            </div>

            <div className="form-row">
              <label>Ranking (optional)</label>
              <input
                type="number"
                min="1"
                max="999"
                value={modal.form.ranking}
                onChange={(e) => setField("ranking", e.target.value)}
                placeholder="Lower number = higher priority"
              />
            </div>

            <div style={{ margin: "16px 0" }}>
              <div style={{ fontSize: 13, fontWeight: 500, color: "#374151", marginBottom: 10 }}>
                Screening criteria (Template 1)
              </div>

              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={modal.form.high_impact}
                  onChange={(e) => setField("high_impact", e.target.checked)}
                />
                High Impact — significant effect on public welfare
              </label>

              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={modal.form.high_developmental}
                  onChange={(e) => setField("high_developmental", e.target.checked)}
                />
                High Developmental — supports national development goals
              </label>

              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={modal.form.pro_poor}
                  onChange={(e) => setField("pro_poor", e.target.checked)}
                />
                Pro-Poor — directly serves low-income sectors
              </label>
            </div>

            <div className="form-actions">
              <button className="btn btn-primary" type="submit">
                {modal.mode === "create" ? "Add system" : "Save changes"}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setModal(null)}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}

function Check({ on }) {
  return (
    <span className={`check-icon ${on ? "check-yes" : "check-no"}`}>
      {on ? "✓" : "—"}
    </span>
  );
}