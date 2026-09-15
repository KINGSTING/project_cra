import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import LandingPage from './LandingPage'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/portal/*" element={<PortalLayout />} />
      </Routes>
    </Router>
  )
}

function PortalLayout() {
  const [role, setRole] = useState('client')
  
  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc', color: '#0f172a', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      <header style={{ background: '#ffffff', borderBottom: '1px solid #e2e8f0', padding: '16px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontWeight: 700, fontSize: '18px', color: '#1e3a8a' }}>IMP-CRA Portal</span>
          <span style={{ fontSize: '12px', background: '#eff6ff', color: '#1d4ed8', padding: '4px 10px', borderRadius: '999px', fontWeight: 600 }}>IMP Handbook Part II-A</span>
        </div>
        <nav style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{ background: '#f1f5f9', padding: '4px', borderRadius: '8px', display: 'flex', gap: '4px' }}>
            <button 
              onClick={() => setRole('client')} 
              style={{ padding: '6px 14px', borderRadius: '6px', border: 'none', background: role === 'client' ? '#ffffff' : 'transparent', boxShadow: role === 'client' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none', fontWeight: 600, cursor: 'pointer', color: role === 'client' ? '#1e3a8a' : '#64748b' }}>
              Agency (Client)
            </button>
            <button 
              onClick={() => setRole('admin')} 
              style={{ padding: '6px 14px', borderRadius: '6px', border: 'none', background: role === 'admin' ? '#ffffff' : 'transparent', boxShadow: role === 'admin' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none', fontWeight: 600, cursor: 'pointer', color: role === 'admin' ? '#1e3a8a' : '#64748b' }}>
              Oversight (Admin)
            </button>
          </div>
          <Link to="/portal/report" style={{ textDecoration: 'none', padding: '8px 16px', background: '#1e3a8a', color: '#fff', borderRadius: '6px', fontWeight: 600, fontSize: '14px' }}>Template 9 Report</Link>
          <Link to="/portal/risks" style={{ textDecoration: 'none', padding: '8px 16px', background: '#3b82f6', color: '#fff', borderRadius: '6px', fontWeight: 600, fontSize: '14px' }}>Risk Register</Link>
        </nav>
      </header>
      
      <main style={{ maxWidth: '1100px', margin: '32px auto', padding: '0 24px' }}>
        <Routes>
          <Route path="/" element={role === 'admin' ? <AdminDashboard /> : <ClientDashboard />} />
          <Route path="report" element={<IMPReport />} />
          <Route path="risks" element={<RiskRegisterDashboard />} />
        </Routes>
      </main>
    </div>
  )
}

function ClientDashboard() {
  const [members, setMembers] = useState([])
  const [form, setForm] = useState({ name: '', designation: '', category: 'chairperson', special_order_ref: '' })
  const [loading, setLoading] = useState(false)
  const clientId = 'DOH_AGENCY'

  const fetchRoster = async () => {
    const res = await fetch(`/api/imc?client_id=${clientId}`)
    const json = await res.json()
    if (json.success) setMembers(json.data)
  }

  useEffect(() => { fetchRoster() }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    await fetch('/api/imc', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form, client_id: clientId })
    })
    setForm({ name: '', designation: '', category: 'chairperson', special_order_ref: '' })
    await fetchRoster()
    setLoading(false)
  }

  const badgeColors = {
    chairperson: { bg: '#fee2e2', text: '#991b1b', label: 'Chairperson' },
    vice_chairperson: { bg: '#fed7aa', text: '#9a3412', label: 'Vice-Chairperson' },
    key_office: { bg: '#e0e7ff', text: '#1e40af', label: 'Key Office' },
    internal_audit: { bg: '#f3e8ff', text: '#6b21a8', label: 'Internal Audit' },
    rank_and_file: { bg: '#e2e8f0', text: '#334155', label: 'Rank-and-file' },
    cso_partner: { bg: '#d1fae5', text: '#065f46', label: 'CSO Partner (Annex 1)' }
  }

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 700, margin: '0 0 8px 0', color: '#0f172a' }}>Integrity Management Committee (IMC) Roster</h2>
        <p style={{ margin: 0, color: '#64748b', fontSize: '14px' }}>Constitutional composition for agency compliance under IMP Part I-Section C Guidelines.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px', alignItems: 'start' }}>
        <div style={{ background: '#ffffff', padding: '24px', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 600, margin: '0 0 16px 0', color: '#1e3a8a' }}>Designate Member</h3>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>Full Name</label>
              <input placeholder="e.g. Juan dela Cruz" value={form.name} onChange={e => setForm({...form, name: e.target.value})} required style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', boxSizing: 'border-box' }} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>Designation / Title</label>
              <input placeholder="e.g. Undersecretary for Admin" value={form.designation} onChange={e => setForm({...form, designation: e.target.value})} required style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', boxSizing: 'border-box' }} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>IMC Role Category</label>
              <select value={form.category} onChange={e => setForm({...form, category: e.target.value})} style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', background: '#fff', boxSizing: 'border-box' }}>
                <option value="chairperson">Chairperson (Head of Institution)</option>
                <option value="vice_chairperson">Vice-Chairperson (&ge; Asst Sec)</option>
                <option value="key_office">Key Office (HR/Finance/Procurement)</option>
                <option value="internal_audit">Internal Audit Head</option>
                <option value="rank_and_file">Rank-and-file Rep</option>
                <option value="cso_partner">CSO Partner (Annex 1)</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>Special Order Ref #</label>
              <input placeholder="SO No. 2026-0012" value={form.special_order_ref} onChange={e => setForm({...form, special_order_ref: e.target.value})} style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', boxSizing: 'border-box' }} />
            </div>
            <button type="submit" disabled={loading} style={{ background: '#1e3a8a', color: '#fff', border: 'none', padding: '12px', borderRadius: '8px', fontWeight: 600, cursor: 'pointer', marginTop: '6px' }}>
              {loading ? 'Saving...' : 'Add to Roster'}
            </button>
          </form>
        </div>

        <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)', overflow: 'hidden' }}>
          <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 600, margin: 0, color: '#1e3a8a' }}>Constitutional Roster ({members.length})</h3>
            <span style={{ fontSize: '12px', color: '#64748b' }}>Client ID: {clientId}</span>
          </div>
          {members.length === 0 ? (
            <div style={{ padding: '48px', textAlign: 'center', color: '#94a3b8' }}>No IMC members designated yet for this agency.</div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr' }}>
              {members.map(m => {
                const badge = badgeColors[m.category] || { bg: '#f1f5f9', text: '#334155', label: m.category }
                return (
                  <div key={m.member_id} style={{ padding: '18px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #f1f5f9' }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '15px', color: '#0f172a' }}>{m.name}</div>
                      <div style={{ fontSize: '13px', color: '#64748b', marginTop: '2px' }}>{m.designation}</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      <span style={{ fontSize: '12px', fontFamily: 'monospace', color: '#475569', background: '#f8fafc', padding: '4px 8px', borderRadius: '4px', border: '1px solid #e2e8f0' }}>{m.special_order_ref || 'No SO ref'}</span>
                      <span style={{ background: badge.bg, color: badge.text, fontSize: '12px', fontWeight: 600, padding: '4px 12px', borderRadius: '999px' }}>{badge.label}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function AdminDashboard() {
  return (
    <div style={{ background: '#ffffff', padding: '32px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
      <h3 style={{ fontSize: '20px', fontWeight: 700, margin: '0 0 12px 0', color: '#1e3a8a' }}>PMC / Technical Secretariat Oversight View</h3>
      <p style={{ color: '#475569', margin: 0 }}>Cross-agency IMC constitution tracking and mandatory compliance verification dashboard.</p>
    </div>
  )
}

function IMPReport() {
  return (
    <div style={{ background: '#ffffff', padding: '32px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
      <h3 style={{ fontSize: '20px', fontWeight: 700, margin: '0 0 12px 0', color: '#1e3a8a' }}>Template 9: Performance Monitoring Report</h3>
    </div>
  )
}

function RiskRegisterDashboard() {
  const [risks, setRisks] = useState([])
  const [form, setForm] = useState({ process_area: '', risk_event: '', likelihood: 2, impact: 3, mitigation_control: '' })
  const clientId = 'DOH_AGENCY'

  const fetchRisks = async () => {
    const res = await fetch(`/api/risk?client_id=${clientId}`)
    const json = await res.json()
    if (json.success) setRisks(json.data)
  }

  useEffect(() => { fetchRisks() }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    await fetch('/api/risk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form, client_id: clientId })
    })
    setForm({ process_area: '', risk_event: '', likelihood: 2, impact: 3, mitigation_control: '' })
    fetchRisks()
  }

  const severityColor = { EXTREME: { bg: '#fee2e2', text: '#991b1b' }, HIGH: { bg: '#ffedd5', text: '#9a3412' }, MODERATE: { bg: '#fef08a', text: '#854d0e' }, LOW: { bg: '#d1fae5', text: '#065f46' } }

  return (
    <div>
      <h2 style={{ fontSize: '24px', fontWeight: 700, margin: '0 0 16px 0', color: '#0f172a' }}>Phase 3: Corruption Risk Register (4x4 Matrix)</h2>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
        <form onSubmit={handleSubmit} style={{ background: '#fff', padding: '24px', borderRadius: '12px', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <input placeholder="Process Area" value={form.process_area} onChange={e => setForm({...form, process_area: e.target.value})} required style={{ padding: '10px', borderRadius: '8px', border: '1px solid #cbd5e1' }} />
          <input placeholder="Risk Event" value={form.risk_event} onChange={e => setForm({...form, risk_event: e.target.value})} required style={{ padding: '10px', borderRadius: '8px', border: '1px solid #cbd5e1' }} />
          <label style={{ fontSize: '12px', fontWeight: 600 }}>Likelihood (1-4): {form.likelihood}</label>
          <input type="range" min="1" max="4" value={form.likelihood} onChange={e => setForm({...form, likelihood: Number(e.target.value)})} />
          <label style={{ fontSize: '12px', fontWeight: 600 }}>Impact (1-4): {form.impact}</label>
          <input type="range" min="1" max="4" value={form.impact} onChange={e => setForm({...form, impact: Number(e.target.value)})} />
          <input placeholder="Mitigation Control" value={form.mitigation_control} onChange={e => setForm({...form, mitigation_control: e.target.value})} style={{ padding: '10px', borderRadius: '8px', border: '1px solid #cbd5e1' }} />
          <button type="submit" style={{ background: '#1e3a8a', color: '#fff', border: 'none', padding: '12px', borderRadius: '8px', fontWeight: 600 }}>Add Risk</button>
        </form>
        <div style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ background: '#f8fafc', textAlign: 'left' }}>
              <tr><th style={{ padding: '12px' }}>Process</th><th style={{ padding: '12px' }}>Event</th><th style={{ padding: '12px' }}>L x I</th><th style={{ padding: '12px' }}>Severity</th></tr>
            </thead>
            <tbody>
              {risks.map(r => {
                const s = severityColor[r.severity] || {}
                return (
                  <tr key={r.risk_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '12px' }}>{r.process_area}</td>
                    <td style={{ padding: '12px' }}>{r.risk_event}</td>
                    <td style={{ padding: '12px' }}>{r.likelihood}x{r.impact} = {r.score}</td>
                    <td style={{ padding: '12px' }}><span style={{ background: s.bg, color: s.text, padding: '4px 8px', borderRadius: '999px', fontWeight: 600, fontSize: '12px' }}>{r.severity}</span></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default App