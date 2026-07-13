import { Link } from "react-router-dom"

const STAT_TILES = [
  ["Total leads", "2,450"],
  ["Calls made", "820"],
  ["Meetings scheduled", "142"],
  ["Reactivated", "128"],
  ["Success rate", "16%"],
]

const OUTCOME_SEGMENTS = [
  ["Reactivated", "#1e5741", 128],
  ["Nurture", "#c98a2b", 96],
  ["Closed-lost", "#b3402f", 54],
  ["No answer", "#8a7a4f", 210],
  ["Needs review", "#9a4d0f", 22],
  ["Unreachable", "#7a6a68", 38],
]

const outcomeTotal = OUTCOME_SEGMENTS.reduce((sum, [, , v]) => sum + v, 0)
const donutGradient = (() => {
  let acc = 0
  const stops = OUTCOME_SEGMENTS.map(([, color, value]) => {
    const start = (acc / outcomeTotal) * 360
    acc += value
    const end = (acc / outcomeTotal) * 360
    return `${color} ${start}deg ${end}deg`
  })
  return `conic-gradient(${stops.join(", ")})`
})()

export default function Dashboard() {
  return (
    <div>
      <div className="page-head">
        <h1>Dashboard</h1>
      </div>

      <div className="stat-grid">
        {STAT_TILES.map(([label, value]) => (
          <div className="stat-card" key={label}>
            <div className="stat-value">{value}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </div>

      <div className="agent-card">
        <div className="agent-head">
          <div>
            <h2 className="agent-title">AI Calling Agent</h2>
            <span className="pill pill-live">Active</span>
          </div>
          <Link to="/leads" className="agent-link">Go to leads</Link>
        </div>

        <div className="agent-meta">Active campaign</div>
        <div className="agent-campaign-name">Admissions Outreach Campaign</div>

        <div className="progress-block">
          <div className="progress-label">
            <span>Daily progress</span>
            <span>450 / 1,000 calls</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: "45%" }} />
          </div>
        </div>

        <div className="agent-columns">
          <div className="panel-box">
            <div className="panel-label">Call volume (today)</div>
            <svg viewBox="0 0 220 90" className="sparkline" preserveAspectRatio="none">
              <polyline
                points="0,70 25,64 50,68 75,52 100,58 125,40 150,44 175,26 200,30 220,14"
                fill="none"
                stroke="var(--pine)"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <div className="panel-box">
            <div className="panel-label">Outcomes</div>
            <div className="donut-block">
              <div className="donut-css" style={{ background: donutGradient }}>
                <div className="donut-hole">
                  <span className="donut-total">{outcomeTotal}</span>
                  <span className="donut-caption">Total</span>
                </div>
              </div>
              <ul className="donut-legend">
                {OUTCOME_SEGMENTS.map(([label, color, value]) => (
                  <li key={label}>
                    <span className="swatch" style={{ background: color }} />
                    {label}
                    <span className="muted">{value}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
