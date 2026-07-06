import { useEffect, useState } from "react"
import { api } from "../api/client"

const CARDS = [
  ["total", "Total leads"],
  ["pending", "Not called yet"],
  ["calling", "Calling now"],
  ["no_answer", "No answer (will retry)"],
  ["qualified", "Qualified"],
  ["not_interested", "Not interested"],
  ["failed", "Unreachable"],
  ["invalid", "Invalid numbers"],
]

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState("")

  const load = async () => {
    try {
      setStats(await api("/api/campaign/stats"))
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    load()
    const timer = setInterval(load, 10000)
    return () => clearInterval(timer)
  }, [])

  if (error) return <div className="error">{error}</div>
  if (!stats) return <div className="muted">Loading...</div>

  const done = stats.total - stats.pending - stats.calling - stats.no_answer
  const progress = stats.total ? Math.round((done / stats.total) * 100) : 0

  return (
    <div>
      <div className="page-head">
        <h1>Dashboard</h1>
        <span className={`pill ${stats.is_running ? "pill-live" : "pill-off"}`}>
          {stats.is_running ? "Campaign running" : "Campaign paused"}
        </span>
      </div>
      <div className="progress-block">
        <div className="progress-label">
          <span>Campaign progress</span>
          <span>{progress}% · {stats.total_calls_made} calls made</span>
        </div>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>
      <div className="stat-grid">
        {CARDS.map(([key, label]) => (
          <div className={`stat-card stat-${key}`} key={key}>
            <div className="stat-value">{stats[key]}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </div>
      <div className="card narrow">
        <h2>Program of interest</h2>
        {(stats.by_program || []).length === 0 && (
          <p className="muted">No program data collected yet.</p>
        )}
        {(stats.by_program || []).map(({ program, count }) => (
          <div className="program-row" key={program}>
            <span>{program}</span>
            <span className="muted">{count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
