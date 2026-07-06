import { useEffect, useState } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import { api } from "../api/client"
import StatusBadge from "../components/StatusBadge"

export default function LeadDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [lead, setLead] = useState(null)
  const [error, setError] = useState("")

  useEffect(() => {
    api(`/api/leads/${id}`).then(setLead).catch((err) => setError(err.message))
  }, [id])

  const deleteLead = async () => {
    if (!window.confirm(`Permanently delete ${lead.full_name || lead.phone}? This also deletes all of their call history and cannot be undone.`)) {
      return
    }
    await api(`/api/leads/${id}`, { method: "DELETE" })
    navigate("/leads")
  }

  if (error) return <div className="error">{error}</div>
  if (!lead) return <div className="muted">Loading...</div>

  return (
    <div>
      <Link to="/leads" className="back">← Back to leads</Link>
      <div className="page-head">
        <h1>{lead.full_name || lead.phone}</h1>
        <div className="actions">
          <StatusBadge status={lead.status} />
          <button className="btn danger" onClick={deleteLead}>Delete lead</button>
        </div>
      </div>
      <div className="detail-grid">
        <div className="card">
          <h2>Collected information</h2>
          <dl>
            <dt>Full name</dt><dd>{lead.full_name || "Not collected"}</dd>
            <dt>Phone</dt><dd>{lead.phone}</dd>
            <dt>Email</dt><dd>{lead.email || "Not collected"}</dd>
            <dt>Program of interest</dt><dd>{lead.program_of_interest || "Not collected"}</dd>
            <dt>Wants callback</dt><dd>{lead.wants_callback ? "Yes" : "No"}</dd>
            <dt>Retry count</dt><dd>{lead.retry_count}</dd>
            <dt>Synced to CRM</dt><dd>{lead.crm_synced ? "Yes" : "Not yet"}</dd>
          </dl>
        </div>
        <div className="card">
          <h2>Call history</h2>
          {lead.calls.length === 0 && <p className="muted">No calls made yet.</p>}
          {lead.calls.map((call) => (
            <div className="call-item" key={call.id}>
              <div className="call-meta">
                <span>{new Date(call.started_at).toLocaleString()}</span>
                <span className="muted">{call.ended_reason || call.status}</span>
                {call.duration_seconds && <span className="muted">{Math.round(call.duration_seconds)}s</span>}
              </div>
              {call.recording_url && (
                <audio controls src={call.recording_url} className="audio" />
              )}
              {call.transcript && (
                <details>
                  <summary>Transcript</summary>
                  <pre className="transcript">{call.transcript}</pre>
                </details>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
