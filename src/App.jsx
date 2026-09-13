import { useState, useEffect } from 'react'

function App() {
  const [assessments, setAssessments] = useState([])
  const [agencyName, setAgencyName] = useState('')
  const [profile, setProfile] = useState('')

  const fetchAssessments = async () => {
    const response = await fetch('/api/assessment')
    const json = await response.json()
    if (json.success) {
      setAssessments(json.data)
    }
  }

  // Fetch data immediately when the page loads
  useEffect(() => {
    fetchAssessments()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Send new data to your Python backend
    await fetch('/api/assessment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        agency_name: agencyName, 
        assessment_profile: profile 
      })
    })
    
    // Clear the form and refresh the list
    setAgencyName('')
    setProfile('')
    fetchAssessments()
  }

  return (
    <div style={{ padding: '40px', fontFamily: 'system-ui, sans-serif', maxWidth: '800px', margin: '0 auto' }}>
      <h2>CRA Tool - Module 1: Context</h2>
      
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '10px', marginBottom: '30px' }}>
        <input 
          type="text" 
          placeholder="Agency Name (e.g. DOH)" 
          value={agencyName} 
          onChange={(e) => setAgencyName(e.target.value)} 
          required 
          style={{ padding: '8px', flex: 1 }}
        />
        <input 
          type="text" 
          placeholder="Assessment Profile" 
          value={profile} 
          onChange={(e) => setProfile(e.target.value)} 
          required 
          style={{ padding: '8px', flex: 1 }}
        />
        <button type="submit" style={{ padding: '8px 16px', cursor: 'pointer' }}>
          Create Assessment
        </button>
      </form>

      <div style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '20px' }}>
        <h3 style={{ marginTop: 0 }}>Active Assessments</h3>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {assessments.map(record => (
            <li key={record.assessment_id} style={{ padding: '10px 0', borderBottom: '1px solid #eee' }}>
              <strong>{record.agency_name}</strong> — {record.assessment_profile} 
              <span style={{ float: 'right', color: '#666' }}>{record.status}</span>
              <br/>
              <small style={{ color: '#aaa' }}>{record.assessment_id}</small>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default App