import httpx
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Lead, LeadStatus
from app.config.settings import settings

SYNCABLE_STATUSES = [LeadStatus.reactivated, LeadStatus.closed_lost, LeadStatus.invalid, LeadStatus.failed]


def get_status(db: Session) -> dict:
    synced = db.query(func.count(Lead.id)).filter(Lead.crm_synced == True).scalar() or 0
    pending = (
        db.query(func.count(Lead.id))
        .filter(Lead.crm_synced == False, Lead.status.in_(SYNCABLE_STATUSES))
        .scalar()
        or 0
    )
    return {
        "configured": bool(settings.crm_webhook_url),
        "synced": synced,
        "pending": pending,
    }


async def sync_finished_leads(db: Session) -> int:
    if not settings.crm_webhook_url:
        return 0
    leads = (
        db.query(Lead)
        .filter(
            Lead.crm_synced == False,
            Lead.status.in_(SYNCABLE_STATUSES),
        )
        .limit(50)
        .all()
    )
    synced = 0
    async with httpx.AsyncClient(timeout=20) as client:
        for lead in leads:
            payload = {
                "full_name": lead.full_name or "Smith",
                "phone": lead.phone,
            }
            try:
                response = await client.post(settings.crm_webhook_url, json=payload)
                if response.status_code < 300:
                    lead.crm_synced = True
                    synced += 1
            except httpx.HTTPError:
                continue
    db.commit()
    return synced
