from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.config.settings import settings
from app.services import qualification_service

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/vapi")
async def vapi_webhook(request: Request, db: Session = Depends(get_db)):
    if settings.vapi_webhook_secret:
        secret = request.headers.get("x-vapi-secret")
        if secret != settings.vapi_webhook_secret:
            raise HTTPException(status_code=401, detail="Invalid webhook secret")
    body = await request.json()
    message = body.get("message", {}) or {}
    if message.get("type") == "end-of-call-report":
        qualification_service.process_call_result(db, message)
    return {"received": True}
