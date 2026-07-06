import { useEffect, useState } from "react"
import { api } from "../api/client"

export default function Campaign() {
  const [campaign, setCampaign] = useState(null)
  const [message, setMessage] = useState("")

  const load = async () => setCampaign(await api("/api/campaign"))

  useEffect(() => {
    load().catch((err) => setMessage(err.message))
  }, [])

  const toggle = async () => {
    const path = campaign.is_running ? "/api/campaign/pause" : "/api/campaign/start"
    setCampaign(await api(path, { method: "POST" }))
  }

  const save = async () => {
    setCampaign(
      await api("/api/campaign", {
        method: "PATCH",
        body: {
          calling_start_hour: campaign.calling_start_hour,
          calling_end_hour: campaign.calling_end_hour,
          max_concurrent_calls: campaign.max_concurrent_calls,
          max_retries: campaign.max_retries,
        },
      })
    )
    setMessage("Settings saved")
  }

  const set = (key) => (e) => setCampaign({ ...campaign, [key]: Number(e.target.value) })

  if (!campaign) return <div className="muted">Loading...</div>

  return (
    <div>
      <div className="page-head">
        <h1>Campaign</h1>
        <button className={`btn ${campaign.is_running ? "danger" : "primary"}`} onClick={toggle}>
          {campaign.is_running ? "Pause campaign" : "Start campaign"}
        </button>
      </div>
      {message && <div className="notice">{message}</div>}
      <div className="card narrow">
        <h2>Calling rules</h2>
        <label>Calling starts at (hour, 0–23)</label>
        <input type="number" min="0" max="23" value={campaign.calling_start_hour} onChange={set("calling_start_hour")} />
        <label>Calling ends at (hour, 0–23)</label>
        <input type="number" min="0" max="23" value={campaign.calling_end_hour} onChange={set("calling_end_hour")} />
        <label>Calls at the same time</label>
        <input type="number" min="1" max="50" value={campaign.max_concurrent_calls} onChange={set("max_concurrent_calls")} />
        <label>Maximum retries per lead</label>
        <input type="number" min="1" max="10" value={campaign.max_retries} onChange={set("max_retries")} />
        <button className="btn primary" onClick={save}>Save changes</button>
      </div>
    </div>
  )
}
