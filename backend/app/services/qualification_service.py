import logging
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Lead, LeadStatus, Call
from app.config.settings import settings
from app.utils.phone import normalize_spoken_email

logger = logging.getLogger("qualification")

NO_ANSWER_REASONS = {
    "customer-did-not-answer",
    "customer-busy",
    "no-answer",
    "voicemail",
    "twilio-failed-to-connect-call",
}
INVALID_REASONS = {"invalid-phone-number", "call-forwarding-not-supported"}


def _extract_structured_output(artifact: dict) -> dict:
    """artifact.structuredOutputs is keyed by structured-output ID (we only ever
    create one, via structured_output_service.py), and Vapi's exact nesting of the
    extracted fields under that key isn't documented — handle both "value is the
    flat data dict directly" and "value wraps it under a result/output/data key"."""
    outputs = artifact.get("structuredOutputs") or {}
    if not outputs:
        return {}
    value = next(iter(outputs.values()), {}) or {}
    for nested_key in ("result", "output", "data"):
        if isinstance(value.get(nested_key), dict):
            return value[nested_key]
    return value


def process_call_result(db: Session, message: dict) -> None:
    call_data = message.get("call", {}) or {}
    vapi_call_id = call_data.get("id")
    # Real phone calls (vapi_service.start_call) put metadata directly on the call via
    # Vapi's REST API, landing at call.metadata. Browser web calls (TestCall.jsx) pass
    # it via assistantOverrides.metadata instead, since the web SDK's start() has no
    # call-level metadata parameter — Vapi stores that under call.assistantOverrides.metadata
    # rather than call.metadata. Check both so either call path can be linked to a lead.
    metadata = call_data.get("metadata") or (call_data.get("assistantOverrides") or {}).get("metadata") or {}
    lead_id = metadata.get("lead_id")
    if not lead_id:
        return
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return

    call = db.query(Call).filter(Call.vapi_call_id == vapi_call_id).first()
    if not call:
        call = Call(lead_id=lead.id, vapi_call_id=vapi_call_id)
        db.add(call)

    ended_reason = message.get("endedReason") or call_data.get("endedReason") or ""
    artifact = message.get("artifact", {}) or {}
    structured = _extract_structured_output(artifact)

    if not structured:
        logger.warning(
            "No structuredOutputs in artifact for lead_id=%d (vapi_call_id=%s) — "
            "raw artifact.structuredOutputs=%r. Falling back to no-answer handling.",
            lead.id, vapi_call_id, artifact.get("structuredOutputs"),
        )
    else:
        found = {k: v for k, v in structured.items() if v not in (None, "", False)}
        logger.info("structuredOutputs found for lead_id=%d: %s", lead.id, found)

    call.status = "ended"
    call.ended_reason = ended_reason
    call.ended_at = datetime.utcnow()
    call.duration_seconds = message.get("durationSeconds")
    call.recording_url = artifact.get("recordingUrl") or message.get("recordingUrl")
    call.transcript = artifact.get("transcript") or message.get("transcript")
    call.extracted_data = structured
    call.cost = message.get("cost")

    logger.info(
        "Full transcript for lead_id=%d (vapi_call_id=%s):\n%s",
        lead.id, vapi_call_id, call.transcript or "(empty)",
    )

    # Extraction models can produce plausible-sounding structuredData even from a
    # near-empty transcript (observed: a call where the caller never said a word
    # still came back with detailed answers for every question). A transcript with
    # no "User:" turn at all means the caller never actually spoke, so nothing in
    # structured can be genuinely grounded — treat it as incomplete regardless of
    # what was extracted, rather than trusting fabricated-looking data.
    has_caller_speech = "User:" in (call.transcript or "")
    if structured and not has_caller_speech:
        logger.warning(
            "structuredOutputs present for lead_id=%d but transcript has no caller "
            "speech (likely fabricated, not grounded) — treating as no-answer. "
            "structured=%s transcript=%r",
            lead.id, structured, call.transcript,
        )
        structured = {}

    if ended_reason in INVALID_REASONS:
        lead.status = LeadStatus.invalid
    elif ended_reason in NO_ANSWER_REASONS:
        _handle_no_answer(lead)
    elif structured:
        _apply_extracted_data(lead, structured, call.transcript or "")
    else:
        _handle_no_answer(lead)

    db.commit()
    logger.info(
        "Call result: lead_id=%d phone=%s ended_reason=%s duration=%ss status=%s%s",
        lead.id, lead.phone, ended_reason, call.duration_seconds, lead.status.value,
        f" review_reason={lead.review_reason!r}" if lead.review_reason else "",
    )


def _handle_no_answer(lead: Lead) -> None:
    lead.retry_count += 1
    if lead.retry_count >= settings.max_retries:
        lead.status = LeadStatus.failed
    else:
        lead.status = LeadStatus.no_answer
        lead.next_retry_at = datetime.utcnow() + timedelta(hours=settings.retry_gap_hours)


def _apply_extracted_data(lead: Lead, data: dict, transcript: str) -> None:
    # These three outcomes only ever happen in the OPENING, before Q1 is ever asked -
    # check and return early BEFORE touching any Q1-Q5 field below. Extraction models
    # can fabricate plausible-sounding answers to questions that were never actually
    # asked (observed live: a call that never got past "I'm busy" still came back with
    # detailed current_status/timeline/original_blocker/enrolled_semester_stage) - the
    # only reliable defense is never persisting those fields when the call structurally
    # couldn't have reached them, regardless of what the extraction claims.
    if _to_bool(data.get("hostile_or_dnc")):
        lead.dnc = True
        lead.status = LeadStatus.closed_lost
        lead.review_reason = "hostile/dnc_requested"
        return

    if _to_bool(data.get("wrong_number")):
        lead.status = LeadStatus.invalid
        lead.review_reason = "wrong_number"
        return

    # reschedule_requested is also set by the extraction model for the "would you like
    # someone to reach out with more information?" callback offered near the end of
    # every non-hot-path branch (see assistant_prompt.py) - not just the opening
    # "I'm busy" case. Only treat it as an opening-only reschedule (discard everything
    # else, retry later) when current_status was never captured, i.e. Q1 was never
    # reached - otherwise the call went all the way through Q1-Q5 and its answers
    # (including a confirmed email) are real and must not be thrown away. Observed live:
    # two calls that fully completed through Q5 with a confirmed email still came back
    # with reschedule_requested=true from the closing-question callback, and had their
    # email silently discarded by this branch.
    if _to_bool(data.get("reschedule_requested")) and not data.get("current_status"):
        reschedule_time = data.get("reschedule_time")
        lead.reschedule_time = str(reschedule_time).strip() if reschedule_time else None
        lead.review_reason = None
        _handle_no_answer(lead)
        return

    # Only reached if the call actually got past the opening.
    lead.current_status = data.get("current_status")
    lead.timeline = data.get("timeline")
    lead.original_blocker = data.get("original_blocker")
    lead.last_qualification = data.get("last_qualification")
    lead.grade_or_cgpa = data.get("grade_or_cgpa")
    lead.meets_baseline = _to_bool(data.get("meets_baseline"))
    lead.advisor_callback_time = data.get("advisor_callback_time")
    if data.get("advisor_callback_email"):
        # Normalize spoken/spelled transcript forms ("name dot x at gmail dot com")
        # into a real address and validate; an email that doesn't survive that is
        # never stored on the lead (the raw value stays visible in
        # call.extracted_data for manual review).
        normalized_email = normalize_spoken_email(str(data.get("advisor_callback_email")))
        if normalized_email:
            lead.email = normalized_email

    timeline = lead.timeline
    enrolled_late = (
        lead.current_status == "enrolled_elsewhere"
        and data.get("enrolled_semester_stage") == "later"
    )

    if timeline == "probably_never" or enrolled_late:
        lead.status = LeadStatus.closed_lost
        lead.review_reason = (
            data.get("probably_never_reason") or "enrolled_elsewhere"
        )
        return

    if timeline == "next_year_or_unsure":
        lead.status = LeadStatus.nurture
        lead.review_reason = lead.original_blocker
        return

    if timeline == "fall_intake":
        if not lead.meets_baseline:
            lead.status = LeadStatus.needs_review
            lead.review_reason = "below_eligibility_baseline"
            return

        if not lead.advisor_callback_time:
            lead.status = LeadStatus.needs_review
            lead.review_reason = "missing: advisor_callback_time"
            return

        lead.route_team = (
            "masters_hybrid" if lead.current_status == "working" else "bachelor"
        )

        if random.random() < settings.qa_sample_rate:
            lead.status = LeadStatus.needs_review
            lead.review_reason = "random_qa_sample"
            return

        lead.status = LeadStatus.reactivated
        lead.review_reason = None
        return

    # Call ended before any branch resolved (e.g. dropped mid-conversation).
    lead.status = LeadStatus.needs_review
    lead.review_reason = "incomplete_call"


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"yes", "true", "haan", "han", "ji", "1"}
    return False
