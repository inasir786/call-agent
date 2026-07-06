import logging
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Lead, LeadStatus, Call
from app.config.settings import settings
from app.utils.phone import is_valid_email
from app.utils.grounding import is_grounded

logger = logging.getLogger("qualification")

NO_ANSWER_REASONS = {
    "customer-did-not-answer",
    "customer-busy",
    "no-answer",
    "voicemail",
    "twilio-failed-to-connect-call",
}
INVALID_REASONS = {"invalid-phone-number", "call-forwarding-not-supported"}


def process_call_result(db: Session, message: dict) -> None:
    call_data = message.get("call", {}) or {}
    vapi_call_id = call_data.get("id")
    metadata = call_data.get("metadata", {}) or {}
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
    analysis = message.get("analysis", {}) or {}
    structured = analysis.get("structuredData") or {}
    artifact = message.get("artifact", {}) or {}

    call.status = "ended"
    call.ended_reason = ended_reason
    call.ended_at = datetime.utcnow()
    call.duration_seconds = message.get("durationSeconds")
    call.recording_url = artifact.get("recordingUrl") or message.get("recordingUrl")
    call.transcript = artifact.get("transcript") or message.get("transcript")
    call.extracted_data = structured
    call.cost = message.get("cost")

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
    name = data.get("full_name") or data.get("name")
    email = data.get("email")
    program = data.get("program_of_interest") or data.get("program")
    interested = _to_bool(data.get("interested"))
    wants_callback = _to_bool(data.get("wants_callback"))

    confidence = {}
    ungrounded_fields = []
    missing_fields = []

    if name:
        lead.full_name = str(name).strip().title()
        grounded = is_grounded(str(name), transcript, field="full_name")
        confidence["full_name"] = {"grounded": grounded}
        if not grounded:
            ungrounded_fields.append("full_name")
    else:
        missing_fields.append("full_name")

    if email and is_valid_email(str(email)):
        lead.email = str(email).strip().lower()
        grounded = is_grounded(str(email), transcript, field="email")
        confidence["email"] = {"grounded": grounded}
        if not grounded:
            ungrounded_fields.append("email")
    else:
        missing_fields.append("email")

    if program:
        lead.program_of_interest = str(program).strip()
        grounded = is_grounded(str(program), transcript, field="program_of_interest")
        confidence["program_of_interest"] = {"grounded": grounded}
        if not grounded:
            ungrounded_fields.append("program_of_interest")
    else:
        missing_fields.append("program_of_interest")

    lead.wants_callback = wants_callback
    lead.field_confidence = confidence

    if not (interested or wants_callback):
        lead.status = LeadStatus.not_interested
        lead.review_reason = None
        return

    if missing_fields or ungrounded_fields:
        reasons = []
        if missing_fields:
            reasons.append(f"missing: {', '.join(missing_fields)}")
        if ungrounded_fields:
            reasons.append(f"ungrounded: {', '.join(ungrounded_fields)}")
        lead.status = LeadStatus.needs_review
        lead.review_reason = "; ".join(reasons)
        return

    if random.random() < settings.qa_sample_rate:
        lead.status = LeadStatus.needs_review
        lead.review_reason = "random_qa_sample"
        return

    lead.status = LeadStatus.qualified
    lead.review_reason = None


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"yes", "true", "haan", "han", "ji", "1"}
    return False
