import { useEffect, useRef, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { api, getToken } from "../api/client"
import StatusBadge from "../components/StatusBadge"

const STATUSES = ["", "pending", "calling", "no_answer", "reactivated", "nurture", "closed_lost", "needs_review", "failed", "invalid"]

export default function Leads() {
  const [searchParams] = useSearchParams()
  const [data, setData] = useState({ total: 0, items: [] })
  const [status, setStatus] = useState(searchParams.get("status") || "")
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(1)
  const [message, setMessage] = useState("")
  const [resetting, setResetting] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const [addName, setAddName] = useState("")
  const [addPhone, setAddPhone] = useState("")
  const [adding, setAdding] = useState(false)
  const [addError, setAddError] = useState("")
  const fileRef = useRef()
  const pageSize = 25

  const load = async () => {
    const params = new URLSearchParams({ page, page_size: pageSize })
    if (status) params.set("status", status)
    if (search) params.set("search", search)
    setData(await api(`/api/leads?${params}`))
  }

  useEffect(() => {
    load().catch((err) => setMessage(err.message))
  }, [status, page])

  const resetAll = async () => {
    if (!window.confirm("Reset ALL leads back to pending — including reactivated, closed-lost, and do-not-call leads? This clears their call outcome (and any DNC lock) and queues them all for re-calling.")) {
      return
    }
    setResetting(true)
    try {
      const result = await api("/api/leads/reset-all", { method: "POST" })
      setMessage(`Reset ${result.reset_count} leads to pending`)
      load()
    } catch (err) {
      setMessage(err.message)
    } finally {
      setResetting(false)
    }
  }

  const deleteLead = async (lead) => {
    if (!window.confirm(`Permanently delete ${lead.full_name || lead.phone}? This also deletes all of their call history and cannot be undone.`)) {
      return
    }
    try {
      await api(`/api/leads/${lead.id}`, { method: "DELETE" })
      setMessage("Lead deleted")
      load()
    } catch (err) {
      setMessage(err.message)
    }
  }

  const doSearch = () => {
    setPage(1)
    load().catch((err) => setMessage(err.message))
  }

  const importCsv = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const form = new FormData()
    form.append("file", file)
    try {
      const result = await api("/api/leads/import", { method: "POST", body: form })
      setMessage(`Imported ${result.imported} leads, skipped ${result.duplicates_skipped} duplicates, ${result.invalid_numbers} invalid numbers`)
      load()
    } catch (err) {
      setMessage(err.message)
    }
    fileRef.current.value = ""
  }

  const openAddModal = () => {
    setAddName("")
    setAddPhone("+")
    setAddError("")
    setShowAddModal(true)
  }

  const submitAddLead = async (e) => {
    e.preventDefault()
    setAdding(true)
    setAddError("")
    try {
      await api("/api/leads", { method: "POST", body: { phone: addPhone, full_name: addName || null } })
      setShowAddModal(false)
      setMessage("Lead added")
      load()
    } catch (err) {
      setAddError(err.message)
    } finally {
      setAdding(false)
    }
  }

  const exportCsv = async (path, filename) => {
    const response = await fetch(path, {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = filename
    link.click()
    URL.revokeObjectURL(url)
  }

  const pages = Math.max(1, Math.ceil(data.total / pageSize))

  return (
    <div>
      <div className="page-head">
        <h1>Leads</h1>
        <div className="actions">
          <input type="file" accept=".csv,.xlsx,.xls" ref={fileRef} onChange={importCsv} hidden />
          <button className="btn" onClick={() => fileRef.current.click()}>Import CSV/Excel</button>
          <button className="btn" onClick={openAddModal}>Add lead</button>
          <button className="btn" onClick={resetAll} disabled={resetting}>
            {resetting ? "Resetting..." : "Reset all to pending"}
          </button>
          <button className="btn" onClick={() => exportCsv("/api/export/all", "all_leads.csv")}>Export all leads</button>
        </div>
      </div>
      {message && <div className="notice">{message}</div>}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Add lead</h2>
            <form onSubmit={submitAddLead}>
              <div className="field">
                <label>Name</label>
                <input value={addName} onChange={(e) => setAddName(e.target.value)} placeholder="Full name (optional)" />
              </div>
              <div className="field">
                <label>Phone number</label>
                <input
                  value={addPhone}
                  onChange={(e) => {
                    const v = e.target.value
                    setAddPhone(v.startsWith("+") ? v : `+${v}`)
                  }}
                  placeholder="+14155551234"
                  required
                  autoFocus
                />
              </div>
              {addError && <div className="notice">{addError}</div>}
              <div className="actions">
                <button type="button" className="btn ghost" onClick={() => setShowAddModal(false)}>Cancel</button>
                <button type="submit" className="btn primary" disabled={adding}>
                  {adding ? "Adding..." : "Add lead"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      <div className="filters">
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }}>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s ? s.replace("_", " ") : "All statuses"}</option>
          ))}
        </select>
        <input
          placeholder="Search name, phone, or email"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && doSearch()}
        />
        <button className="btn" onClick={doSearch}>Search</button>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Phone</th>
            <th>Current status</th>
            <th>Timeline</th>
            <th>Status</th>
            <th>Advisor callback</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((lead) => (
            <tr key={lead.id}>
              <td>{lead.full_name || <span className="muted">Unknown</span>}</td>
              <td>{lead.phone}</td>
              <td>{lead.current_status || <span className="muted">—</span>}</td>
              <td>{lead.timeline || <span className="muted">—</span>}</td>
              <td><StatusBadge status={lead.status} /></td>
              <td>{lead.advisor_callback_time || <span className="muted">—</span>}</td>
              <td>
                <Link to={`/leads/${lead.id}`}>View</Link>
                {" · "}
                <a href="#" onClick={(e) => { e.preventDefault(); deleteLead(lead) }} className="danger-link">Delete</a>
              </td>
            </tr>
          ))}
          {data.items.length === 0 && (
            <tr><td colSpan="7" className="muted center">No leads yet. Import a CSV to begin.</td></tr>
          )}
        </tbody>
      </table>
      <div className="pager">
        <button className="btn" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
        <span className="muted">Page {page} of {pages} · {data.total} leads</span>
        <button className="btn" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</button>
      </div>
    </div>
  )
}
