from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import Lead, LeadStatus, Campaign
from app.config.settings import settings


def get_campaign(db: Session) -> Campaign:
    campaign = db.query(Campaign).first()
    if not campaign:
        campaign = Campaign(
            is_running=False,
            calling_start_hour=settings.calling_start_hour,
            calling_end_hour=settings.calling_end_hour,
            max_concurrent_calls=settings.max_concurrent_calls,
            max_retries=settings.max_retries,
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
    return campaign


def set_running(db: Session, running: bool) -> Campaign:
    campaign = get_campaign(db)
    campaign.is_running = running
    db.commit()
    db.refresh(campaign)
    return campaign


def update_settings(db: Session, updates: dict) -> Campaign:
    campaign = get_campaign(db)
    for key, value in updates.items():
        if value is not None and hasattr(campaign, key):
            setattr(campaign, key, value)
    db.commit()
    db.refresh(campaign)
    return campaign


def set_schedule(db: Session, when: datetime) -> Campaign:
    campaign = get_campaign(db)
    campaign.scheduled_start_at = when
    campaign.is_running = False
    db.commit()
    db.refresh(campaign)
    return campaign


def cancel_schedule(db: Session) -> Campaign:
    campaign = get_campaign(db)
    campaign.scheduled_start_at = None
    db.commit()
    db.refresh(campaign)
    return campaign


def apply_due_schedule(db: Session, campaign: Campaign) -> Campaign:
    if campaign.is_running or not campaign.scheduled_start_at:
        return campaign
    now = datetime.now(ZoneInfo(settings.timezone)).replace(tzinfo=None)
    if now >= campaign.scheduled_start_at:
        campaign.is_running = True
        campaign.scheduled_start_at = None
        db.commit()
        db.refresh(campaign)
    return campaign


def within_calling_hours(campaign: Campaign) -> bool:
    now = datetime.now(ZoneInfo(settings.timezone))
    return campaign.calling_start_hour <= now.hour < campaign.calling_end_hour


def pick_next_leads(db: Session, limit: int) -> list[Lead]:
    now = datetime.utcnow()
    return (
        db.query(Lead)
        .filter(
            or_(
                Lead.status == LeadStatus.pending,
                (Lead.status == LeadStatus.no_answer) & (Lead.next_retry_at <= now),
            )
        )
        .order_by(Lead.id)
        .limit(limit)
        .all()
    )


def count_active_calls(db: Session) -> int:
    return db.query(Lead).filter(Lead.status == LeadStatus.calling).count()
