# Session Report — 2026-07-07

## Summary

Today's work took the assistant from a simple linear qualification script to a full 5-question branching admissions-reactivation flow, switched and re-tuned the voice pipeline twice, and fixed a chain of increasingly deep bugs that were silently preventing call data from ever being saved — ending with a confirmed, successful real phone call that reached the correct final outcome.

---

## 1. Call flow redesign

Replaced the old flow (greet → name → email → program → interest → callback) with a 5-step branching script matching the "NIT | Powered by ASU — Old & Cold Lead Reactivation" design:

- **Opening** → busy/wrong-number/hostile handling
- **Q1** current status (deciding/enrolled elsewhere/working)
- **Q2** timeline (this Fall / next year / probably never)
- **Q3** original blocker (cost / competitor / timing) — nurture path
- **Q4** eligibility (last qualification + grade/CGPA, self-assessed against a configurable baseline)
- **Q5** financial lever + advisor handoff (books a callback time)

Email collection was dropped from the live call script (per your decision, the `email` column/CSV import/exports were kept as-is, just not asked for live anymore).

### New outcome model
Replaced `qualified` / `not_interested` with three new statuses: **`reactivated`**, **`nurture`**, **`closed_lost`** — plus a hard **DNC lock** (separate `dnc` boolean) for hostile callers, which permanently excludes them from the dialer and from "reset all to pending."

### New data captured per lead
`current_status`, `timeline`, `original_blocker`, `last_qualification`, `grade_or_cgpa`, `meets_baseline`, `advisor_callback_time`, `route_team` (bachelor vs. masters/hybrid), `reschedule_time` — all added as new `Lead` columns, migrated onto the live Postgres DB.

### Prompt refinements made over the day
- Injected the caller's real name into the greeting (with a generic fallback), but restricted it to **only the opening line** — the assistant kept re-adopting names callers said mid-call ("Adi"/"Addie"), which is now blocked.
- Added a rule to answer in-script questions directly (scholarships, ASU pathway, etc.) and redirect anything else to a fallback phone number (0300-0000000), instead of guessing.
- Added an explicit rule to never restart the call/repeat the greeting when a response is unclear — ask for clarification and stay on the same question instead.
- Fixed a real bug where the busy-branch's follow-up question ("call back later?") could be misread as permission to continue the flow — now defaults to "still unavailable" unless the caller unambiguously says to continue.
- Fixed Q3 not actually continuing into Q4 (it was ending the call early) with an explicit "you MUST continue" directive.
- Injected **today's actual date** into the prompt, since the model had no way to judge whether a caller's stated year meant "this Fall" or "next year" without it.
- Simplified the greeting wording and enforced "simple English" phrasing.
- Language handling was extended to English/Urdu bilingual, then reverted back to English-only at your request.
- End-of-call behavior went through several iterations: originally disabled (assistant must never hang up) → re-enabled at your request → had to add an explicit "never narrate the function call out loud" rule after the model started literally saying "use functions dot end call" instead of silently invoking it.

---

## 2. Voice pipeline — switched twice

- Started on the realtime speech-to-speech model (`gpt-realtime`).
- Diagnosed real reliability problems: calls silence-timing out, sentences getting clipped before finishing, and confirmed via Vapi's own docs that **turn-detection/interruption isn't configurable at all for realtime models** — it's handled internally with no exposed levers.
- Switched to the cascading pipeline (Deepgram `nova-2` transcriber + `gpt-4o` + 11labs voice), which restored working, tunable turn-taking (`stopSpeakingPlan`). Also tuned voice quality settings (`stability`, `optimizeStreamingLatency`, multilingual model) after a reported audio-quality issue.
- Per your explicit final request, switched back to the realtime model. Flagged the known risk of reintroducing the earlier issues before making the change.

---

## 3. Bugs found and fixed (roughly in the order discovered)

1. **CSV import crash** — a ragged row (extra trailing comma) made `csv.DictReader` hand back a list instead of a string for the overflow column, crashing the import. Fixed with a value-normalizing helper.
2. **CSV import silently importing garbage** — a stray blank leading row before the real header caused the importer to treat the blank row as the header, losing every name. Fixed by scanning for the first row with ≥2 named columns.
3. **TestCall.jsx "KrispSDK is duplicated" / call ejection** — traced to a real race condition: the "Start test call" button wasn't disabled synchronously, so a fast second click (or a call ending and being retried quickly) could spin up two concurrent Vapi/Daily sessions. Fixed with a synchronous status flip plus a timestamp-based cooldown covering all teardown paths (manual stop, call-end event, and pre-start cleanup).
4. **Every single test call's data silently failing to save** — traced through several layers:
   - Metadata (`lead_id`) wasn't reaching the webhook at all for browser test calls — Vapi stores it at `call.assistantOverrides.metadata` for web calls, not `call.metadata` like real phone calls. Fixed by checking both locations.
   - Even after that, `structuredData` never populated. Root cause, found by pulling Vapi's actual OpenAPI spec: **the entire `analysisPlan.structuredDataPlan` mechanism we were using is marked deprecated in Vapi's API** and silently returns nothing. Rebuilt the whole extraction path on the current mechanism — a separately-created `StructuredOutput` resource referenced via `artifactPlan.structuredOutputIds`, with results landing in `call.artifact.structuredOutputs` instead.
   - Along the way, also fixed two JSON-schema issues that would have blocked the old mechanism anyway (a literal `null` mixed into `enum` arrays, and later confirmed the correct schema shape has no nullable-type unions or forced `required` fields at all, per Vapi's own documented example).
5. **Assistant narrating its own tool call** — instead of silently hanging up, it said "use functions dot end call" out loud. Added an explicit rule forbidding any mention of tools/functions/mechanism in speech.
6. **Fabricated structured data** — one call's transcript showed the caller never said a word, yet the extraction still produced detailed, plausible-sounding answers for every question. Added a sanity check: if the transcript has no real caller turn at all, discard any structured data as ungrounded and fall back to no-answer handling, regardless of what was extracted.
7. **"Reset all to pending" only cleared status/retry fields**, leaving every previously-collected field behind. Extended it to wipe every collected field back to blank, as requested.
8. **Test/dummy lead reachable by the real dialer** — the reusable "Smith" test lead (used to verify the webhook pipeline from the browser Test Call page) was excluded from `pick_next_leads()` so a real campaign run can never accidentally dial it.

---

## 4. New capability: Test Call page now verifies the real pipeline

Previously, the browser Test Call page only exercised the prompt/voice — no webhook, nothing saved anywhere. It now:
- Uses a single reusable "Smith" test lead (reset to a clean blank state on every preview fetch).
- Passes that lead's ID through as call metadata, so the real webhook → qualification pipeline runs exactly as it would for a real phone call.
- Shows a direct link to that lead's detail page so you can check the saved result right after a test call ends.

Also added: full transcript logging to the console for every call (in addition to the existing extracted-data and final-status logs), so you can see exactly what was said and how it was interpreted without querying the database.

---

## 5. Testing performed

- Multiple browser Test Call sessions exercising the opening branches (yes / busy / wrong number / hostile), the full Q1→Q5 flow, eligibility assessment, the scholarship question, and advisor callback booking.
- One confirmed **real phone call** (via the live campaign/dialer) to an actual lead completed successfully end-to-end: real conversation → correct structured-data extraction → correct final status (`reactivated`) — validating the entire redesigned pipeline works outside of the browser test environment too.

---

## 6. Known open items / residual risk

- Realtime model's lack of configurable turn-detection is a platform limitation, not something fixable from our side — worth watching closely on the next round of testing now that it's back in use.
- The fabrication safety net only catches the "caller never spoke at all" case — a real conversation where the model invents one wrong detail among otherwise-correct ones wouldn't be caught, since per-field grounding checks were deliberately dropped for the new categorical fields earlier in the redesign.
- The dialer still retries busy/reschedule callers on the generic retry schedule, not at the specific time they requested.
