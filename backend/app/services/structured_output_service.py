import logging
import httpx
from app.config.settings import settings

logger = logging.getLogger("structured_output")

VAPI_BASE_URL = "https://api.vapi.ai"
STRUCTURED_OUTPUT_NAME = "nit_reactivation_flow"

_structured_output_id: str | None = None


def get_structured_output_id() -> str | None:
    """Cached ID of the Vapi StructuredOutput resource used for call analysis.

    analysisPlan.structuredDataPlan (the old inline-schema mechanism) is marked
    deprecated in Vapi's own API and was silently never returning any data — the
    current mechanism is a separately-created StructuredOutput resource, referenced
    on the assistant via artifactPlan.structuredOutputIds. Created/updated once here
    (at app startup) rather than per-call, since it's account-level, not call-level,
    state.
    """
    return _structured_output_id


def ensure_structured_output(schema: dict, description: str | None = None) -> str | None:
    global _structured_output_id
    if not settings.vapi_api_key:
        return None
    headers = {"Authorization": f"Bearer {settings.vapi_api_key}"}
    try:
        with httpx.Client(timeout=20) as client:
            existing = client.get(
                f"{VAPI_BASE_URL}/structured-output",
                headers=headers,
                params={"name": STRUCTURED_OUTPUT_NAME},
            )
            existing.raise_for_status()
            results = existing.json()
            items = results.get("results", results) if isinstance(results, dict) else results
            match = next((item for item in items if item.get("name") == STRUCTURED_OUTPUT_NAME), None)

            if match:
                _structured_output_id = match["id"]
                if match.get("schema") != schema or (description and match.get("description") != description):
                    update = client.patch(
                        f"{VAPI_BASE_URL}/structured-output/{match['id']}",
                        headers=headers,
                        json={"schema": schema, "description": description},
                    )
                    update.raise_for_status()
                    logger.info("Updated structured output %s with current schema", match["id"])
                return _structured_output_id

            created = client.post(
                f"{VAPI_BASE_URL}/structured-output",
                headers=headers,
                json={"name": STRUCTURED_OUTPUT_NAME, "schema": schema, "description": description},
            )
            created.raise_for_status()
            _structured_output_id = created.json()["id"]
            logger.info("Created structured output %s", _structured_output_id)
            return _structured_output_id
    except httpx.HTTPError as exc:
        logger.error("Failed to ensure structured output exists: %s", exc)
        return None


def ensure_assistant_structured_output(assistant_id: str) -> None:
    """Attach the ensured StructuredOutput to a saved dashboard assistant.

    Calls made with assistantId use the assistant exactly as stored in Vapi — the
    inline artifactPlan from build_assistant() never applies. Without the structured
    output attached, end-of-call reports carry no structuredOutputs and every
    completed call degrades to no-answer handling in qualification_service. This
    re-attaches on every startup (additive PATCH, only the artifactPlan field), so a
    dashboard edit that drops it heals on the next restart. Best-effort: failures are
    logged, never fatal to startup.
    """
    if not (assistant_id and _structured_output_id and settings.vapi_api_key):
        return
    headers = {"Authorization": f"Bearer {settings.vapi_api_key}"}
    try:
        with httpx.Client(timeout=20) as client:
            resp = client.get(f"{VAPI_BASE_URL}/assistant/{assistant_id}", headers=headers)
            resp.raise_for_status()
            plan = resp.json().get("artifactPlan") or {}
            ids = plan.get("structuredOutputIds") or []
            if _structured_output_id in ids:
                return
            plan["structuredOutputIds"] = ids + [_structured_output_id]
            update = client.patch(
                f"{VAPI_BASE_URL}/assistant/{assistant_id}",
                headers=headers,
                json={"artifactPlan": plan},
            )
            update.raise_for_status()
            logger.info(
                "Attached structured output %s to assistant %s",
                _structured_output_id, assistant_id,
            )
    except httpx.HTTPError as exc:
        logger.error(
            "Failed to attach structured output to assistant %s: %s", assistant_id, exc
        )
