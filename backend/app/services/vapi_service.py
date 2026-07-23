import httpx
from app.config.settings import settings
from app.services.assistant_prompt import build_assistant, FIRST_MESSAGE_WITH_NAME

VAPI_BASE_URL = "https://api.vapi.ai"


async def start_call(phone: str, lead_id: int, full_name: str | None = None) -> dict:
    payload = {
        "phoneNumberId": settings.vapi_phone_number_id,
        "customer": {"number": phone},
        "metadata": {"lead_id": lead_id},
    }
    if settings.vapi_assistant_id:
        # Use the saved dashboard assistant — its own prompt, voice, transcriber, and
        # server URL apply, so dashboard edits take effect without a code deploy. Only
        # the greeting is personalized per call; the assistant's own firstMessage is
        # the generic (no-name) variant and stays in effect when the lead has no name.
        payload["assistantId"] = settings.vapi_assistant_id
        if full_name and full_name.strip():
            first_name = full_name.strip().split()[0]
            payload["assistantOverrides"] = {
                "firstMessage": FIRST_MESSAGE_WITH_NAME.format(first_name=first_name)
            }
    else:
        payload["assistant"] = build_assistant(full_name)
    headers = {"Authorization": f"Bearer {settings.vapi_api_key}"}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{VAPI_BASE_URL}/call", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
