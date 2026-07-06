import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models import Lead, LeadStatus
from app.utils.security import require_admin

router = APIRouter(prefix="/api/export", tags=["export"], dependencies=[Depends(require_admin)])


@router.get("/qualified")
def export_qualified(db: Session = Depends(get_db)):
    leads = (
        db.query(Lead)
        .filter(Lead.status == LeadStatus.qualified)
        .order_by(Lead.updated_at.desc())
        .all()
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Full Name", "Phone", "Email", "Program of Interest", "Wants Callback", "Updated At"])
    for lead in leads:
        writer.writerow([
            lead.full_name or "",
            lead.phone,
            lead.email or "",
            lead.program_of_interest or "",
            "Yes" if lead.wants_callback else "No",
            lead.updated_at.strftime("%Y-%m-%d %H:%M"),
        ])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=qualified_leads.csv"},
    )


@router.get("/all")
def export_all(db: Session = Depends(get_db)):
    leads = db.query(Lead).order_by(Lead.updated_at.desc()).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Full Name", "Phone", "Email", "Program of Interest", "Status", "Wants Callback", "Updated At"])
    for lead in leads:
        writer.writerow([
            lead.full_name or "",
            lead.phone,
            lead.email or "",
            lead.program_of_interest or "",
            lead.status.value,
            "Yes" if lead.wants_callback else "No",
            lead.updated_at.strftime("%Y-%m-%d %H:%M"),
        ])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=all_leads.csv"},
    )
