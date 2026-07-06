from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.schemas.schemas import CampaignOut, CampaignUpdate, CampaignSchedule, StatsOut
from app.services import campaign_service, lead_service
from app.utils.security import require_admin

router = APIRouter(prefix="/api/campaign", tags=["campaign"], dependencies=[Depends(require_admin)])


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    campaign = campaign_service.get_campaign(db)
    data = lead_service.get_stats(db)
    data["is_running"] = campaign.is_running
    return data


@router.get("", response_model=CampaignOut)
def get_campaign(db: Session = Depends(get_db)):
    return campaign_service.get_campaign(db)


@router.post("/start", response_model=CampaignOut)
def start(db: Session = Depends(get_db)):
    return campaign_service.set_running(db, True)


@router.post("/pause", response_model=CampaignOut)
def pause(db: Session = Depends(get_db)):
    return campaign_service.set_running(db, False)


@router.patch("", response_model=CampaignOut)
def update(payload: CampaignUpdate, db: Session = Depends(get_db)):
    return campaign_service.update_settings(db, payload.model_dump())


@router.post("/schedule", response_model=CampaignOut)
def schedule(payload: CampaignSchedule, db: Session = Depends(get_db)):
    return campaign_service.set_schedule(db, payload.scheduled_start_at)


@router.post("/schedule/cancel", response_model=CampaignOut)
def cancel_schedule(db: Session = Depends(get_db)):
    return campaign_service.cancel_schedule(db)
