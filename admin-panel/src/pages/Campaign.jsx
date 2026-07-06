import { useEffect, useState } from "react"
import { api } from "../api/client"

export default function Campaign() {
  const [campaign, setCampaign] = useState(null)
  const [message, setMessage] = useState("")
  const [scheduleInput, setScheduleInput] = useState("")

  const load = async () => setCampaign(await api("/api/campaign"))

  useEffect(() => {
    load().catch((err) => setMessage(err.message))
  }, [])

  useEffect(() => {
    if (!campaign?.scheduled_start_at) return
    const timer = setInterval(load, 15000)
    return () => clearInterval(timer)
  }, [campaign?.scheduled_start_at])

  const toggle = async () => {
    const path = campaign.is_running ? "/api/campaign/pause" : "/api/campaign/start"
    setCampaign(await api(path, { method: "POST" }))
  }

  const schedule = async () => {
    if (!scheduleInput) return
    try {
      setCampaign(await api("/api/campaign/schedule", {
        method: "POST",
        body: { scheduled_start_at: scheduleInput },
      }))
      setMessage(`Campaign will start automatically at ${new Date(scheduleInput).toLocaleString()}`)
    } catch (err) {
      setMessage(err.message)
    }
  }

  const cancelSchedule = async () => {
    setCampaign(await api("/api/campaign/schedule/cancel", { method: "POST" }))
    setScheduleInput("")
    setMessage("Scheduled start cancelled")
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
          {campaign.is_running ? "Pause campaign" : "Start now"}
        </button>
      </div>
      {campaign.scheduled_start_at && (
        <div className="notice">
          Scheduled to start automatically at {new Date(campaign.scheduled_start_at).toLocaleString()}
        </div>
      )}
      {message && <div className="notice">{message}</div>}
      <div className="card narrow">
        <h2>Scheduled start</h2>
        <label>Start campaign automatically at</label>
        <input
          type="datetime-local"
          value={scheduleInput}
          onChange={(e) => setScheduleInput(e.target.value)}
        />
        <div className="actions">
          <button className="btn primary" onClick={schedule} disabled={!scheduleInput}>Schedule</button>
          {campaign.scheduled_start_at && (
            <button className="btn" onClick={cancelSchedule}>Cancel schedule</button>
          )}
        </div>
      </div>
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
