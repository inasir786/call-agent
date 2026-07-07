import { useEffect, useState } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import { api } from "../api/client"
import StatusBadge from "../components/StatusBadge"

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
          {lead.dnc && <span className="badge badge-closed_lost">Do Not Call</span>}
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
            <button className="btn primary" disabled={reviewing} onClick={() => reviewLead("reactivated")}>Confirm reactivated</button>
            <button className="btn" disabled={reviewing} onClick={() => reviewLead("nurture")}>Move to nurture</button>
            <button className="btn" disabled={reviewing} onClick={() => reviewLead("closed_lost")}>Confirm closed-lost</button>
          </div>
        </div>
      )}
      <div className="detail-grid">
        <div className="card">
          <h2>Collected information</h2>
          {lead.calls.length === 0 && (
            <p className="muted">No call has been made to this lead yet — every field below will stay "null" until a call completes.</p>
          )}
          <dl>
            <dt>Full name</dt><dd>{lead.full_name || "null"}</dd>
            <dt>Phone</dt><dd>{lead.phone}</dd>
            <dt>Reason</dt><dd>{lead.review_reason || "null"}</dd>
            <dt>Do not call</dt><dd>{lead.dnc ? "Yes" : "No"}</dd>
            <dt>Current status</dt><dd>{lead.current_status || "null"}</dd>
            <dt>Timeline</dt><dd>{lead.timeline || "null"}</dd>
            <dt>Original blocker</dt><dd>{lead.original_blocker || "null"}</dd>
            <dt>Last qualification</dt><dd>{lead.last_qualification || "null"}</dd>
            <dt>Grade / CGPA</dt><dd>{lead.grade_or_cgpa || "null"}</dd>
            <dt>Meets eligibility baseline</dt>
            <dd>{lead.meets_baseline === null || lead.meets_baseline === undefined ? "null" : (lead.meets_baseline ? "Yes" : "No")}</dd>
            <dt>Route team</dt><dd>{lead.route_team || "null"}</dd>
            <dt>Advisor callback time</dt><dd>{lead.advisor_callback_time || "null"}</dd>
            <dt>Requested callback time</dt><dd>{lead.reschedule_time || "null"}</dd>
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
