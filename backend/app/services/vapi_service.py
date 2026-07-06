import httpx
from app.config.settings import settings
from app.services.assistant_prompt import build_assistant

VAPI_BASE_URL = "https://api.vapi.ai"


async def start_call(phone: str, lead_id: int) -> dict:
    payload = {
        "assistant": build_assistant(),
        "phoneNumberId": settings.vapi_phone_number_id,
        "customer": {"number": phone},
        "metadata": {"lead_id": lead_id},
    }
    headers = {"Authorization": f"Bearer {settings.vapi_api_key}"}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{VAPI_BASE_URL}/call", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
