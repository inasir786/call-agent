import { useEffect, useState } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import { api } from "../api/client"
import StatusBadge from "../components/StatusBadge"

function fieldWarning(lead, field) {
  const confidence = lead.field_confidence || {}
  if (confidence[field] && confidence[field].grounded === false) {
    return <span className="warning-glyph" title="Could not verify this value against the transcript">⚠</span>
  }
  return null
}

export default function LeadDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [lead, setLead] = useState(null)
  const [error, setError] = useState("")
  const [reviewing, setReviewing] = useState(false)

  const load = () => api(`/api/leads/${id}`).then(setLead).catch((err) => setError(err.message))

  useEffect(() => {
    load()
  }, [id])

  const deleteLead = async () => {
    if (!window.confirm(`Permanently delete ${lead.full_name || lead.phone}? This also deletes all of their call history and cannot be undone.`)) {
      return
    }
    await api(`/api/leads/${id}`, { method: "DELETE" })
    navigate("/leads")
  }

  const reviewLead = async (decision) => {
    setReviewing(true)
    try {
      await api(`/api/leads/${id}/review`, { method: "PATCH", body: { decision } })
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setReviewing(false)
    }
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
      {lead.status === "needs_review" && (
        <div className="notice">
          <strong>Flagged for review:</strong> {lead.review_reason === "random_qa_sample"
            ? "randomly selected for quality-assurance spot-check"
            : lead.review_reason}
          <div className="actions" style={{ marginTop: 10 }}>
            <button className="btn primary" disabled={reviewing} onClick={() => reviewLead("qualified")}>Confirm qualified</button>
            <button className="btn" disabled={reviewing} onClick={() => reviewLead("not_interested")}>Confirm not interested</button>
          </div>
        </div>
      )}
      <div className="detail-grid">
        <div className="card">
          <h2>Collected information</h2>
          <dl>
            <dt>Full name</dt><dd>{lead.full_name || "Not collected"} {fieldWarning(lead, "full_name")}</dd>
            <dt>Phone</dt><dd>{lead.phone}</dd>
            <dt>Email</dt><dd>{lead.email || "Not collected"} {fieldWarning(lead, "email")}</dd>
            <dt>Program of interest</dt><dd>{lead.program_of_interest || "Not collected"} {fieldWarning(lead, "program_of_interest")}</dd>
            <dt>Wants callback</dt><dd>{lead.wants_callback ? "Yes" : "No"}</dd>
            <dt>Retry count</dt><dd>{lead.retry_count}</dd>
            <dt>Synced to CRM</dt><dd>{lead.crm_synced ? "Yes" : "Not yet"}</dd>
            {lead.reviewed_at && (
              <>
                <dt>Reviewed</dt>
                <dd>{new Date(lead.reviewed_at).toLocaleString()}{lead.reviewed_by ? ` by ${lead.reviewed_by}` : ""}</dd>
              </>
            )}
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
