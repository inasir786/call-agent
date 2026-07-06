import csv
import io
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Lead, LeadStatus, Call
from app.utils.phone import normalize_pk_phone


def import_leads_csv(db: Session, file_bytes: bytes) -> dict:
    text = file_bytes.decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))
    imported = 0
    duplicates = 0
    invalid = 0
    seen = set()
    existing = {p for (p,) in db.query(Lead.phone).all()}
    for row in reader:
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        phone_key = next(
            (k for k in row if "phone" in k or "mobile" in k or "contact" in k or "number" in k),
            None,
        )
        phone = normalize_pk_phone(row.get(phone_key, "")) if phone_key else None
        if not phone:
            for value in row.values():
                phone = normalize_pk_phone(value)
                if phone:
                    break
        if not phone:
            invalid += 1
            continue
        if phone in seen or phone in existing:
            duplicates += 1
            continue
        seen.add(phone)
        lead = Lead(
            phone=phone,
            full_name=row.get("name") or row.get("full_name") or None,
            email=row.get("email") or None,
            program_of_interest=row.get("program") or row.get("program_of_interest") or None,
            crm_id=row.get("crm_id") or row.get("id") or None,
        )
        db.add(lead)
        imported += 1
    db.commit()
    return {"imported": imported, "duplicates_skipped": duplicates, "invalid_numbers": invalid}


def reset_all_leads(db: Session) -> int:
    updated = (
        db.query(Lead)
        .update(
            {Lead.status: LeadStatus.pending, Lead.retry_count: 0, Lead.next_retry_at: None},
            synchronize_session=False,
        )
    )
    db.commit()
    return updated


def get_stats(db: Session) -> dict:
    counts = dict(
        db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all()
    )
    total_calls = db.query(func.count(Call.id)).scalar() or 0
    program_counts = (
        db.query(Lead.program_of_interest, func.count(Lead.id))
        .filter(Lead.program_of_interest.isnot(None), Lead.program_of_interest != "")
        .group_by(Lead.program_of_interest)
        .order_by(func.count(Lead.id).desc())
        .all()
    )
    return {
        "total": sum(counts.values()),
        "pending": counts.get(LeadStatus.pending, 0),
        "calling": counts.get(LeadStatus.calling, 0),
        "no_answer": counts.get(LeadStatus.no_answer, 0),
        "qualified": counts.get(LeadStatus.qualified, 0),
        "not_interested": counts.get(LeadStatus.not_interested, 0),
        "invalid": counts.get(LeadStatus.invalid, 0),
        "failed": counts.get(LeadStatus.failed, 0),
        "total_calls_made": total_calls,
        "by_program": [{"program": program, "count": count} for program, count in program_counts],
    }
