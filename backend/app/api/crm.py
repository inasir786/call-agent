from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.schemas.schemas import CrmStatusOut, CrmSyncResult
from app.services import crm_service
from app.utils.security import require_admin

router = APIRouter(prefix="/api/crm", tags=["crm"], dependencies=[Depends(require_admin)])


@router.get("/status", response_model=CrmStatusOut)
def status(db: Session = Depends(get_db)):
    return crm_service.get_status(db)


@router.post("/sync", response_model=CrmSyncResult)
async def sync(db: Session = Depends(get_db)):
    synced = await crm_service.sync_finished_leads(db)
    return {"synced": synced}
