from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.config.settings import settings
from app.services.assistant_prompt import build_assistant
from app.services.lead_service import get_or_reset_test_lead
from app.utils.security import require_admin

router = APIRouter(prefix="/api/assistant", tags=["assistant"], dependencies=[Depends(require_admin)])


@router.get("/preview")
def preview_assistant(db: Session = Depends(get_db)):
    # Reuse a single fixed "Malaika" lead so a browser test call goes through the exact
    # same webhook -> qualification pipeline as a real call, letting you verify data
    # actually lands in the database (check /leads/<test_lead_id> after the call) —
    # reset to a clean pending state on every preview fetch so stale data from a
    # previous test doesn't linger.
    test_lead = get_or_reset_test_lead(db)
    assistant = build_assistant(test_lead.full_name)
    if not settings.vapi_server_url:
        # No webhook URL configured at all — nothing would receive the end-of-call
        # report anyway, so there's no point keeping metadata/server wired up.
        assistant.pop("server", None)
    return {
        "assistant": assistant,
        # When set, the test page starts the call with this saved assistant ID (same
        # path real phone calls take) instead of the inline assistant above. Note the
        # Malaika email read-back override in build_assistant() can't be injected into
        # a saved assistant, so it doesn't apply in that mode.
        "assistant_id": settings.vapi_assistant_id or None,
        "public_key": settings.vapi_public_key,
        "test_lead_id": test_lead.id,
    }
