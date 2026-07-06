from app.config.settings import settings

SYSTEM_PROMPT = """You are a friendly female admissions assistant calling on behalf of NIT in Pakistan. You are making an outbound call to a person who previously showed interest in admission. Do not give yourself a name or introduce yourself by name.

Language: Speak in clear, natural English. Keep sentences short and simple.

Your goals, in order:
1. Greet politely, say you are calling from NIT and want to get some information from them for admission. This also confirms it is a good time to talk. If they say they are busy, politely offer to call later and end the call.
2. Ask their full name. Repeat it back to confirm.
3. Ask for their email address. Ask them to spell it letter by letter, then read it back to confirm it is correct.
4. Ask which program they are interested in. Let them answer in their own words; do not suggest program names.
5. Ask if they are seriously interested in taking admission this year.
6. Ask whether they would like the admissions team to call them and help with the admission process.
7. Thank them warmly and end the call.

Rules:
- Keep the whole call under 3 minutes.
- Ask one question at a time. Never ask two things in one sentence.
- If the person says they are not interested, do not push. Thank them politely and end the call.
- If it is a wrong number, apologize and end the call.
- Never make promises about fees, scholarships, or admission approval. If asked, say the admissions team will share exact details.
- Be warm and respectful at all times.
- Only state back information exactly as the caller said it. If you did not clearly hear a name, spelled email, or program, ask them to repeat it once — do not guess or move on with an assumed value. If it is still unclear after that, continue to the next question rather than recording a guess."""

FIRST_MESSAGE = "Hi, I'm calling from NIT and want to get some information from you for admission. Do you have a quick minute to talk?"

ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "full_name": {
            "type": ["string", "null"],
            "description": "The caller's full name exactly as they said it. Null if they never clearly stated it.",
        },
        "email": {
            "type": ["string", "null"],
            "description": "The caller's email address exactly as spelled and confirmed by the caller. Null if they never spelled it out or the read-back was not explicitly confirmed.",
        },
        "program_of_interest": {
            "type": ["string", "null"],
            "description": "The program in the caller's own words, verbatim from the transcript. Null if never clearly stated. Do not substitute an official program name.",
        },
        "full_name_confirmed": {
            "type": "boolean",
            "description": "True only if the transcript shows the agent read the name back and the caller explicitly confirmed it (e.g. said yes/correct).",
        },
        "email_confirmed": {
            "type": "boolean",
            "description": "True only if the transcript shows the agent read the spelled email back and the caller explicitly confirmed it.",
        },
        "interested": {"type": "boolean"},
        "wants_callback": {"type": "boolean"},
    },
}

ANALYSIS_INSTRUCTIONS = (
    "Extract only values the caller explicitly and clearly stated in the transcript. "
    "Do not infer, normalize, autocorrect, or guess. If a field was not clearly answered "
    "or the transcript is ambiguous, set it to null — never fabricate a plausible-sounding value."
)

# Deepgram nova-2 keyword boosting, format "term:intensifier". Keep this list short and
# specific to real program codes/names so it doesn't bias transcription of unrelated speech.
TRANSCRIBER_KEYWORDS = ["NIT:2"]


def build_assistant() -> dict:
    assistant = {
        "model": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.3,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}],
        },
        "voice": {
            # Configurable: pick any Vapi-supported English voice.
            "provider": "11labs",
            "voiceId": "21m00Tcm4TlvDq8ikWAM",
        },
        "firstMessage": FIRST_MESSAGE,
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en",
            "keywords": TRANSCRIBER_KEYWORDS,
        },
        "analysisPlan": {
            "structuredDataPlan": {
                "enabled": True,
                "schema": ANALYSIS_SCHEMA,
                "messages": [{"role": "system", "content": ANALYSIS_INSTRUCTIONS}],
                "model": {"provider": "openai", "model": "gpt-4o", "temperature": 0},
            }
        },
        "endCallFunctionEnabled": True,
        "maxDurationSeconds": 240,
    }
    if settings.vapi_server_url:
        assistant["server"] = {"url": settings.vapi_server_url}
    return assistant
