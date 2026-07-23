from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models import Lead, LeadStatus
from app.schemas.schemas import LeadListOut, LeadDetailOut, LeadOut, LeadCreate, ImportResult, ResetResult, ReviewDecision
from app.services import lead_service
from app.utils.security import require_admin

router = APIRouter(prefix="/api/leads", tags=["leads"], dependencies=[Depends(require_admin)])


@router.post("/import", response_model=ImportResult)
async def import_leads(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Please upload a CSV or Excel (.xlsx/.xls) file")
    content = await file.read()
    return lead_service.import_leads_csv(db, content, file.filename)


@router.post("", response_model=LeadOut)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    try:
        return lead_service.create_lead(db, payload.phone, payload.full_name)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/reset-all", response_model=ResetResult)
def reset_all(db: Session = Depends(get_db)):
    return {"reset_count": lead_service.reset_all_leads(db)}


@router.get("", response_model=LeadListOut)
def list_leads(
    status: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Lead)
    if status:
        query = query.filter(Lead.status == status)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            Lead.phone.ilike(pattern)
            | Lead.full_name.ilike(pattern)
            | Lead.email.ilike(pattern)
        )
    total = query.count()
    items = query.order_by(Lead.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "items": items}


@router.get("/{lead_id}", response_model=LeadDetailOut)
def lead_detail(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}/review", response_model=LeadDetailOut)
def review_lead(lead_id: int, payload: ReviewDecision, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if payload.decision not in ("reactivated", "nurture", "closed_lost"):
        raise HTTPException(status_code=400, detail="decision must be 'reactivated', 'nurture', or 'closed_lost'")
    lead.status = LeadStatus(payload.decision)
    lead.review_reason = None
    lead.reviewed_at = datetime.utcnow()
    lead.reviewed_by = payload.reviewed_by
    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(lead)
    db.commit()
    return {"deleted": True}
