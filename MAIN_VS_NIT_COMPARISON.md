# Comparison: `main` branch vs. current working tree (branch `NIT`)

`NIT` has no commits of its own yet — every change below is currently **uncommitted** in the working directory. This document goes file-by-file: what `main` had, what changed, and why.

Overall: **24 modified files, 4 new files**, 607 insertions / 178 deletions (code only, excluding the two new markdown reports).

---

## New files

| File | Purpose |
|---|---|
| `backend/app/api/assistant.py` | New `GET /api/assistant/preview` endpoint — builds the live assistant config plus a reusable "Smith" test lead, for the browser Test Call page. |
| `backend/app/services/structured_output_service.py` | Creates/updates a Vapi `StructuredOutput` resource (the current, non-deprecated data-extraction mechanism) and caches its ID. |
| `admin-panel/src/pages/TestCall.jsx` | Browser-based WebRTC test-call page (mic test, live transcript, raw event log). |
| `SESSION_REPORT_2026-07-07.md` | Narrative summary of today's work. |

---

## Backend

### `backend/app/models/lead.py`
- `LeadStatus` enum: **removed** `qualified`, `not_interested` → **added** `reactivated`, `nurture`, `closed_lost`.
- New `Lead` columns: `reschedule_time`, `current_status`, `timeline`, `original_blocker`, `last_qualification`, `grade_or_cgpa`, `meets_baseline`, `advisor_callback_time`, `route_team`, `dnc`.

### `backend/app/schemas/schemas.py`
- `LeadOut`: added all the new `Lead` fields above, plus `dnc: bool`.
- `StatsOut`: `qualified`/`not_interested` → `reactivated`/`nurture`/`closed_lost`, added `needs_review` (previously never counted at all — a pre-existing gap fixed along the way).

### `backend/app/config/settings.py` / `backend/.env.example`
- Added `vapi_public_key` (needed for the new browser Test Call page's WebRTC connection).
- Added `eligibility_baseline_description` — a configurable sentence (default: "a CGPA of 2.0 out of 4.0, 50% marks, or an equivalent pass grade or higher") the assistant self-assesses callers against for Q4.

### `backend/app/services/assistant_prompt.py` (biggest single diff — 211 lines changed)
- **Prompt**: entirely replaced the old linear script (greet → name → email → program → interest → callback) with the 5-question branching flow (Opening → Q1 status → Q2 timeline → Q3 blocker → Q4 eligibility → Q5 financial lever/handoff), plus today's date injected so "this Fall" can be judged against a real calendar, plus a long list of behavioral rules added incrementally (no restarting on unclear input, name used only once, answer in-script questions or redirect to a fallback number, must end the call silently after the closing line, never narrate the end-call mechanism).
- **Extraction schema**: replaced the old 8-field schema (name/email/program/interested/wants_callback/reschedule) with a 14-field schema matching the new flow (`current_status`, `timeline`, `original_blocker`, `last_qualification`, `grade_or_cgpa`, `meets_baseline`, `advisor_callback_time`, etc.), rewritten twice more over the day to fix schema-compliance issues (removed `null` from `enum` arrays; removed forced `required`/`additionalProperties` after confirming Vapi's actual documented schema shape doesn't use nullable-type unions at all).
- **`build_assistant()` signature**: now takes `full_name: str | None` and interpolates it into a personalized greeting (with a generic fallback).
- **Model/voice/transcriber**: swapped `gpt-4o-mini` → `gpt-realtime-2025-08-28` (realtime speech-to-speech), 11labs Rachel → OpenAI `marin` voice, and removed the Deepgram transcriber block entirely (realtime models process audio natively). *Mid-session this was reversed to the cascading pipeline (Deepgram + `gpt-4o` + tuned 11labs voice) after diagnosing reliability problems with realtime, then switched back to realtime at the end of the day per explicit request — the file currently reflects the realtime configuration.*
- **`analysisPlan.structuredDataPlan` → `artifactPlan.structuredOutputIds`**: the old mechanism is confirmed deprecated in Vapi's own API spec and was silently returning nothing; replaced with a reference to the `StructuredOutput` resource created by the new `structured_output_service.py`.

### `backend/app/services/qualification_service.py` (second-biggest diff — 174 lines changed)
- Removed the old grounding-based extraction (`is_grounded`, `is_valid_email` checks on name/email/program).
- `process_call_result()`: now reads structured data from `artifact.structuredOutputs` (new helper `_extract_structured_output()`) instead of `analysis.structuredData`; checks for `lead_id` in both `call.metadata` (real phone calls) and `call.assistantOverrides.metadata` (browser web calls — a Vapi quirk specific to that call path); added full-transcript console logging and a warning log when structured data comes back empty; added a fabrication guard that discards structured data entirely if the transcript shows no actual caller speech.
- `_apply_extracted_data()`: entirely rewritten as a decision table driven by the new fields — `hostile_or_dnc` → DNC lock + `closed_lost`; `wrong_number` → `invalid`; `reschedule_requested` → retried like a no-answer; `timeline == probably_never` or "enrolled elsewhere, late semester" → `closed_lost`; `timeline == next_year_or_unsure` → `nurture`; `timeline == fall_intake` → gated on `meets_baseline` and a booked `advisor_callback_time` before reaching `reactivated` (with the existing random QA-sample override still applied on top).

### `backend/app/services/lead_service.py`
- Fixed two real CSV-import bugs: a ragged row crashing on a list-vs-string type error, and a leading blank row causing the real header to be misread as data.
- New `TEST_LEAD_PHONE` constant + `get_or_reset_test_lead()` — a single reusable "Smith" lead for the Test Call page, reset to a clean blank state every time it's fetched.
- `reset_all_leads()`: previously only reset `status`/`retry_count`/`next_retry_at`; now also wipes every collected field (email, program, all the new Q1–Q5 fields, review_reason, etc.) back to blank, and excludes DNC-locked leads from the reset entirely.
- `get_stats()`: updated for the new status names, added the missing `needs_review` count.

### `backend/app/services/campaign_service.py`
- `pick_next_leads()`: added `Lead.dnc.is_(False)` (don't ever call DNC-locked leads) and excludes `TEST_LEAD_PHONE` (the "Smith" fixture must never be dialed by a real campaign).

### `backend/app/services/crm_service.py`
- `SYNCABLE_STATUSES`: `qualified`/`not_interested` → `reactivated`/`closed_lost`.
- Outgoing CRM payload simplified from 6 fields down to just `full_name` (defaulting to `"Smith"` if blank) and `phone`.

### `backend/app/services/vapi_service.py` / `backend/app/workers/dialer_worker.py`
- `start_call()` now takes `full_name` and threads it through to `build_assistant()`; the dialer passes `lead.full_name` when starting each call.

### `backend/app/api/leads.py`
- `review_lead()`'s decision whitelist: `qualified`/`not_interested` → `reactivated`/`nurture`/`closed_lost`.

### `backend/app/api/export.py`
- "Qualified" export now filters on `reactivated`; both CSV exports swap `program_of_interest`/`wants_callback` columns for `route_team`/`advisor_callback_time`.

### `backend/app/main.py`
- Registers the new `assistant` router.
- Calls `ensure_structured_output()` at startup, before the dialer loop starts, so the `StructuredOutput` resource exists (or gets updated) before any calls are placed.

---

## Frontend (`admin-panel/`)

- **`App.jsx` / `Layout.jsx`**: new `/test-call` route and nav link.
- **`StatusBadge.jsx` / `Dashboard.jsx` / `Leads.jsx`**: status labels, dashboard stat cards, and the leads-table status filter all updated for `reactivated`/`nurture`/`closed_lost` (dropping `qualified`/`not_interested`); `Leads.jsx`'s table also swaps its Email/Program columns for Current-status/Timeline, and its "reset all" confirmation text now mentions DNC leads are excluded.
- **`LeadDetail.jsx`**: removed the old grounding-warning glyph (`⚠`) system (no longer computed on the backend for the new categorical fields); "Collected information" now always shows every field (falling back to the literal text `"null"` rather than hiding rows), plus a `Reason` row, a `Do not call` row, and a DNC badge in the page header; the review banner's two buttons (Confirm qualified/Confirm not interested) became three (Confirm reactivated / Move to nurture / Confirm closed-lost).
- **`styles.css`**: badge/stat-card color classes renamed to match the new status set.
- **`package.json`**: added `@vapi-ai/web` (the WebRTC SDK powering the new Test Call page).
- **`README.md`**: documents `VAPI_PUBLIC_KEY` and the new Test Call page as a new numbered section (renumbering the rest of the setup guide).

---

## Net effect

`main` is a single linear qualification script (name/email/program/interest/callback → qualified/not_interested) with no way to test the save pipeline except a real phone call. The working tree is a full 5-question branching reactivation campaign with a richer data model, a DNC compliance lock, a corrected (and previously silently-broken) data-extraction mechanism, and a browser-based test harness that exercises the exact same save pipeline as a real call.
