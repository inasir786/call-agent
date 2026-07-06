import asyncio
import logging
from app.config.database import SessionLocal
from app.models import LeadStatus
from app.services import campaign_service, vapi_service, crm_service

logger = logging.getLogger("dialer")

LOOP_INTERVAL_SECONDS = 15


async def dialer_loop():
    while True:
        try:
            await _tick()
        except Exception as exc:
            logger.exception("Dialer tick failed: %s", exc)
        await asyncio.sleep(LOOP_INTERVAL_SECONDS)


async def _tick():
    db = SessionLocal()
    try:
        campaign = campaign_service.get_campaign(db)
        campaign = campaign_service.apply_due_schedule(db, campaign)
        if not campaign.is_running:
            return
        if not campaign_service.within_calling_hours(campaign):
            return
        active = campaign_service.count_active_calls(db)
        slots = campaign.max_concurrent_calls - active
        if slots <= 0:
            return
        leads = campaign_service.pick_next_leads(db, slots)
        for lead in leads:
            try:
                await vapi_service.start_call(lead.phone, lead.id)
                lead.status = LeadStatus.calling
                db.commit()
            except Exception as exc:
                logger.error("Failed to start call for lead %s: %s", lead.id, exc)
                lead.status = LeadStatus.failed
                db.commit()
        await crm_service.sync_finished_leads(db)
    finally:
        db.close()
