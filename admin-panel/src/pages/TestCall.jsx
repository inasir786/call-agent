import { useEffect, useRef, useState } from "react"
import { Link } from "react-router-dom"
import Vapi from "@vapi-ai/web"
import { api } from "../api/client"

// Vapi's "error" event payload isn't always a plain Error — sometimes it's a
// plain object ({}) whose message lives one or two levels deeper, or an Event.
// Try the common shapes before falling back to a full JSON dump.
function describeError(err) {
  if (!err) return "Unknown error"
  if (typeof err === "string") return err
  const message = err.message || err.error?.message || err.errorMsg || err.reason
  if (typeof message === "string" && message) return message
  try {
    return JSON.stringify(err, Object.getOwnPropertyNames(err))
  } catch {
    return String(err)
  }
}

export default function TestCall() {
  const [status, setStatus] = useState("idle") // idle | connecting | active | ended
  const [lines, setLines] = useState([])
  const [live, setLive] = useState(null)
  const [error, setError] = useState("")
  const [micLevel, setMicLevel] = useState(0)
  const [micSpeaking, setMicSpeaking] = useState(false)
  const [eventLog, setEventLog] = useState([])
  const [micTestLevel, setMicTestLevel] = useState(0)
  const [micTestActive, setMicTestActive] = useState(false)
  const [micTestError, setMicTestError] = useState("")
  const [testLeadId, setTestLeadId] = useState(null)
  const vapiRef = useRef(null)
  const micTestStreamRef = useRef(null)
  const micTestAudioCtxRef = useRef(null)
  const micTestRafRef = useRef(null)
  // Timestamp of the last time a Vapi/Daily call object was torn down (via any path:
  // the call-end event, the manual stop button, or start()'s own pre-cleanup). Daily's
  // underlying iframe/WebRTC teardown can lag behind the moment we learn the call has
  // ended, so start() enforces a minimum cooldown since this timestamp before creating
  // a new call object — otherwise it risks the "KrispSDK is duplicated" ejection bug
  // (VapiAI/client-sdk-web#70), which can happen even when vapiRef.current is already
  // null (e.g. right after call-end fires) — relying on the ref alone isn't enough.
  const lastTeardownAtRef = useRef(0)
  const CALL_TEARDOWN_COOLDOWN_MS = 800

  const logEvent = (text) => {
    const stamp = new Date().toLocaleTimeString()
    setEventLog((prev) => [...prev.slice(-49), `${stamp}  ${text}`])
  }

  const stopMicTest = async () => {
    if (micTestRafRef.current) cancelAnimationFrame(micTestRafRef.current)
    micTestStreamRef.current?.getTracks().forEach((t) => t.stop())
    // Awaited (not fire-and-forget): starting a real Vapi call right after this needs
    // the mic device fully released first, or Daily's WebRTC layer can fail to attach
    // its own audio processor ("error applying mic processor") on a still-busy device.
    if (micTestAudioCtxRef.current) {
      try {
        await micTestAudioCtxRef.current.close()
      } catch {
        // already closed
      }
    }
    micTestStreamRef.current = null
    micTestAudioCtxRef.current = null
    micTestRafRef.current = null
    setMicTestActive(false)
    setMicTestLevel(0)
  }

  // Bypasses Vapi entirely: raw getUserMedia + an AnalyserNode volume meter.
  // If this bar never moves, the problem is the browser/OS/hardware mic path,
  // not anything in Vapi's config — narrows down where to look next.
  const startMicTest = async () => {
    setMicTestError("")
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      micTestStreamRef.current = stream
      const AudioCtx = window.AudioContext || window.webkitAudioContext
      const audioCtx = new AudioCtx()
      micTestAudioCtxRef.current = audioCtx
      const source = audioCtx.createMediaStreamSource(stream)
      const analyser = audioCtx.createAnalyser()
      analyser.fftSize = 512
      source.connect(analyser)
      const data = new Uint8Array(analyser.frequencyBinCount)
      setMicTestActive(true)
      const tick = () => {
        analyser.getByteTimeDomainData(data)
        let sumSquares = 0
        for (let i = 0; i < data.length; i++) {
          const v = (data[i] - 128) / 128
          sumSquares += v * v
        }
        const rms = Math.sqrt(sumSquares / data.length)
        setMicTestLevel(Math.min(1, rms * 4))
        micTestRafRef.current = requestAnimationFrame(tick)
      }
      tick()
    } catch (err) {
      setMicTestError(describeError(err) || "Could not access microphone")
    }
  }

  useEffect(() => {
    return () => {
      vapiRef.current?.stop()
      stopMicTest()
    }
  }, [])

  const start = async () => {
    // Flip status first, synchronously, before any await — this is the only thing
    // that hides the "Start test call" button. If this were delayed until after an
    // async step (as it previously was), the button stays clickable during that
    // window and a second click re-enters start() while the first is still running,
    // creating two concurrent Vapi/Daily call objects — which is what causes Daily's
    // "KrispSDK is duplicated" warning and an immediate ejection of the session.
    if (status === "connecting" || status === "active") return
    setStatus("connecting")
    // If a previous call (e.g. from a page refresh mid-call, which skips the
    // unmount cleanup) is still hanging around, tear it down first — starting
    // a second session while one lingers is what causes Daily to report
    // error.type "ejected" on the new one. This must be awaited: Vapi's stop()
    // calls the underlying Daily call object's destroy().
    if (vapiRef.current) {
      await vapiRef.current.stop()
      vapiRef.current = null
      lastTeardownAtRef.current = Date.now()
    }
    // Enforce a minimum cooldown since the last teardown (from any path — this one,
    // the manual stop button, or the call-end event) before creating a new call
    // object, since Daily's browser-side iframe/WebRTC teardown can lag behind the
    // moment we learn the previous call ended. See CALL_TEARDOWN_COOLDOWN_MS comment.
    const sinceTeardown = Date.now() - lastTeardownAtRef.current
    if (sinceTeardown < CALL_TEARDOWN_COOLDOWN_MS) {
      await new Promise((resolve) => setTimeout(resolve, CALL_TEARDOWN_COOLDOWN_MS - sinceTeardown))
    }
    await stopMicTest()
    setError("")
    setLines([])
    setLive(null)
    setMicLevel(0)
    setMicSpeaking(false)
    setEventLog([])
    setTestLeadId(null)
    try {
      const { assistant, public_key, test_lead_id } = await api("/api/assistant/preview")
      if (!public_key) {
        setError("VAPI_PUBLIC_KEY is not set in the backend .env")
        setStatus("idle")
        return
      }
      setTestLeadId(test_lead_id)
      const vapi = new Vapi(public_key)
      vapiRef.current = vapi

      vapi.on("call-start", () => {
        setStatus("active")
        logEvent("call-start")
      })
      vapi.on("call-end", () => {
        setStatus("ended")
        setLive(null)
        setMicSpeaking(false)
        logEvent("call-end")
        vapiRef.current = null
        lastTeardownAtRef.current = Date.now()
      })
      vapi.on("error", (err) => {
        const detail = describeError(err)
        setError(detail)
        setStatus("idle")
        logEvent(`error: ${detail}`)
      })
      // volume-level/speech-start/speech-end reflect raw mic input, independent of
      // whether Deepgram manages to turn it into text — use them to tell "mic never
      // reached Vapi" apart from "audio arrived but wasn't transcribed".
      vapi.on("volume-level", (level) => setMicLevel(level))
      vapi.on("speech-start", () => {
        setMicSpeaking(true)
        logEvent("speech-start (voice detected)")
      })
      vapi.on("speech-end", () => {
        setMicSpeaking(false)
        logEvent("speech-end")
      })
      vapi.on("message", (message) => {
        if (message.type !== "transcript") {
          logEvent(`message: ${message.type}${message.role ? " (" + message.role + ")" : ""}`)
          return
        }
        const { role, transcript: text, transcriptType } = message
        logEvent(`transcript ${transcriptType} [${role}]: ${text || ""}`)
        if (!text) return

        if (transcriptType !== "final") {
          // Live/partial transcript for the utterance currently being spoken.
          // Deepgram keeps overwriting this until it finalizes (or never finalizes
          // for very short utterances like "yes") — show it live either way.
          setLive({ role, text })
          return
        }

        setLive(null)
        setLines((prev) => {
          const last = prev[prev.length - 1]
          if (last && last.role === role) {
            // Vapi sends the assistant's own speech as several finalized chunks
            // (roughly one per sentence/clause) — merge consecutive same-speaker
            // chunks into a single continuous line instead of one line each.
            const merged = [...prev]
            merged[merged.length - 1] = { role, text: `${last.text} ${text}`.trim() }
            return merged
          }
          return [...prev, { role, text }]
        })
      })

      // Passing lead_id as metadata here (not on the assistant object itself) is what
      // makes it show up in the end-of-call-report webhook's call.metadata, the same
      // field process_call_result() reads for real phone calls — this is what lets
      // this test call go through the exact same DB-writing pipeline as a real one.
      await vapi.start(assistant, { metadata: { lead_id: test_lead_id } })
    } catch (err) {
      setError(describeError(err))
      setStatus("idle")
    }
  }

  const stop = async () => {
    setStatus("ended")
    // Don't null vapiRef.current here — leave it to start()'s own cleanup path
    // (which awaits stop() before nulling) so a fast "Start test call" click right
    // after "End call" still goes through that same safe teardown instead of racing
    // a fresh Vapi/Daily instance against this one's destroy().
    await vapiRef.current?.stop()
    lastTeardownAtRef.current = Date.now()
  }

  return (
    <div>
      <div className="page-head">
        <h1>Test call</h1>
      </div>
      <div className="card narrow">
        <h2>Step 1: test your microphone{micTestActive ? " — listening" : ""}</h2>
        <p className="muted" style={{ marginBottom: 8 }}>
          Checks your browser/OS mic access directly, with no Vapi call involved.
          Do this first if your voice wasn't picked up in a call.
        </p>
        <div className="progress-bar" style={{ marginBottom: 12 }}>
          <div
            className="progress-fill"
            style={{ width: `${Math.round(micTestLevel * 100)}%`, transition: "width 80ms linear" }}
          />
        </div>
        <div className="actions">
          {!micTestActive
            ? <button className="btn" onClick={startMicTest}>Test microphone</button>
            : <button className="btn" onClick={stopMicTest}>Stop mic test</button>}
        </div>
        {micTestError && <div className="error">{micTestError}</div>}
      </div>
      <div className="card narrow" style={{ marginTop: 20 }}>
        <h2>Step 2: talk to the assistant in your browser</h2>
        <p className="muted">
          Uses the exact assistant config from assistant_prompt.py, no phone number needed.
          Allow microphone access when prompted.
        </p>
        {testLeadId && (
          <p className="muted" style={{ marginTop: 8 }}>
            This test call is linked to a reusable test lead named "Smith" — once the call
            ends, check <Link to={`/leads/${testLeadId}`}>its lead detail page</Link> to
            verify the extracted data actually saved to the database.
          </p>
        )}
        <div className="actions" style={{ marginTop: 14 }}>
          {status !== "active" && status !== "connecting" && (
            <button className="btn primary" onClick={start}>Start test call</button>
          )}
          {(status === "active" || status === "connecting") && (
            <button className="btn danger" onClick={stop}>End call</button>
          )}
        </div>
        {status === "connecting" && <p className="muted" style={{ marginTop: 12 }}>Connecting...</p>}
        {status === "active" && <div className="notice" style={{ marginTop: 12 }}>Call in progress, speak into your microphone.</div>}
        {status === "ended" && <p className="muted" style={{ marginTop: 12 }}>Call ended.</p>}
        {error && <div className="error">{error}</div>}
      </div>
      {(status === "active" || status === "connecting") && (
        <div className="card narrow" style={{ marginTop: 20 }}>
          <h2>Mic input {micSpeaking ? "— voice detected" : ""}</h2>
          <p className="muted" style={{ marginBottom: 8 }}>
            This bar reflects raw microphone audio reaching Vapi, before any transcription.
            If it never moves while you talk, it's a mic/permission issue, not a transcription one.
          </p>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${Math.min(100, Math.round(micLevel * 100))}%`, transition: "width 80ms linear" }}
            />
          </div>
        </div>
      )}
      <div className="card narrow" style={{ marginTop: 20 }}>
        <h2>Live transcript</h2>
        {lines.length === 0 && !live && <p className="muted">No transcript yet.</p>}
        {lines.map((line, i) => (
          <div className={`transcript-line role-${line.role}`} key={i}>
            <span className="role">{line.role === "assistant" ? "Assistant" : "You"}:</span> {line.text}
          </div>
        ))}
        {live && (
          <div className={`transcript-line role-${live.role} live`}>
            <span className="role">{live.role === "assistant" ? "Assistant" : "You"}:</span> {live.text}
          </div>
        )}
      </div>
      <div className="card narrow" style={{ marginTop: 20 }}>
        <h2>Raw event log</h2>
        {eventLog.length === 0 && <p className="muted">No events yet.</p>}
        <pre className="transcript">{eventLog.join("\n")}</pre>
      </div>
    </div>
  )
}
