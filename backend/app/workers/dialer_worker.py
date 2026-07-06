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
            logger.debug("Tick skipped: campaign is not running")
            return
        if not campaign_service.within_calling_hours(campaign):
            logger.debug("Tick skipped: outside calling hours")
            return
        active = campaign_service.count_active_calls(db)
        slots = campaign.max_concurrent_calls - active
        if slots <= 0:
            logger.debug("Tick skipped: no free slots (%d/%d active)", active, campaign.max_concurrent_calls)
            return
        leads = campaign_service.pick_next_leads(db, slots)
        logger.info(
            "Tick: %d active call(s), %d slot(s) free, %d lead(s) picked to call",
            active, slots, len(leads),
        )
        for lead in leads:
            try:
                result = await vapi_service.start_call(lead.phone, lead.id)
                lead.status = LeadStatus.calling
                db.commit()
                logger.info(
                    "Call started: lead_id=%d phone=%s vapi_call_id=%s",
                    lead.id, lead.phone, result.get("id"),
                )
            except Exception as exc:
                logger.error("Failed to start call for lead_id=%d phone=%s: %s", lead.id, lead.phone, exc)
                lead.status = LeadStatus.failed
                db.commit()
        synced = await crm_service.sync_finished_leads(db)
        if synced:
            logger.info("CRM sync: %d lead(s) synced", synced)
    finally:
        db.close()
