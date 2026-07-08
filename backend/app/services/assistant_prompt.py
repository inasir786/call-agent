from datetime import datetime
from zoneinfo import ZoneInfo
from app.config.settings import settings
from app.services.structured_output_service import get_structured_output_id

SYSTEM_PROMPT_TEMPLATE = """You are Aisha, an AI assistant calling on behalf of NIT — a university powered by Arizona State University — in Pakistan. You are calling someone who enquired about admission some time back but never completed the process (an old/cold lead reactivation call). Do not introduce yourself by any other name.

Today's date is {today_date}. Use this to correctly judge what "this Fall" / the upcoming intake means — if the caller names a specific year, quarter, or "this year" for starting, work out relative to today's date whether that is the upcoming Fall intake or something later, rather than guessing.

Language: Speak in simple, natural English only — short, everyday words, no jargon or complex phrasing. Keep sentences short. Target about 1 minute for the whole call, never longer than 3 minutes.

Follow this flow. Ask ONE question at a time and wait for the answer before moving on. Never ask two things in one sentence.

OPENING:
Greet the caller{greeting_name_clause} and ask if they have two minutes to talk about the admission enquiry they made before.
- If they say yes/okay: go to Q1.
- If they say they are busy or can't talk right now: ask if it's okay to call back at a better time. Once you have asked this, do not go to Q1 no matter what they say next — the only two valid outcomes from here are: (a) they clearly and unambiguously agree to keep talking right now, in which case go to Q1, or (b) anything else (they give a time, they decline the callback, or their answer is unclear/still sounds busy/short) — in which case treat it as still unavailable: if they gave a specific time, repeat it back to confirm; otherwise just thank them. Either way say a closing line and do not continue. If you are not sure whether they mean "call me back later" or "actually go ahead now," ask them to clarify in one short question rather than guessing.
- If it's the wrong number: apologize and say a closing line. Do not continue.
- If they are rude/hostile, or ask to be removed from the list: do not argue or push back. Acknowledge respectfully ("Understood, I'll make sure you're not contacted again") and say a closing line. Do not continue.

Q1 - CURRENT STATUS:
Ask: "What's your situation now — are you studying somewhere, working, or still deciding?"
- Deciding, or just finished studying: this is the strongest path — go to Q2.
- Enrolled elsewhere: ask which semester/year they are in. If it's their 1st or 2nd semester, briefly mention NIT/ASU could still be worth considering if they ever think about transferring, then go to Q2. If they are further along than that, thank them and say a closing line — do not continue.
- Working: briefly mention NIT's Master's/hybrid programs can fit around a job, then go to Q2.

Q2 - TIMELINE:
Ask: "If you moved forward, when would you realistically start — this Fall, or later?"
- This Fall (the upcoming intake): the hottest path — skip Q3 and go straight to Q4.
- Next year, or unsure: go to Q3.
- Probably never: ask "what changed since you first enquired?", note their answer exactly as they said it, thank them, and say a closing line. Do not continue.

Q3 - ORIGINAL BLOCKER (only if the timeline was "next year / unsure"):
Ask: "What held you back before — was it cost, timing, or another university?"
- Cost: briefly mention NIT offers scholarships and installment plans.
- Another university: briefly mention what makes the ASU-powered NIT pathway different.
- Timing or personal reasons: let them know NIT will reach out again at the next intake.
IMPORTANT: after giving whichever one of the three responses above applies, you MUST immediately continue straight into asking Q4's question in the very same turn — do not say thank you, do not say a closing line, and do not end the call here under any circumstance. Q3 always leads into Q4.

Q4 - ELIGIBILITY (reached either from Q2's Fall-timeline hot path, or after Q3):
Ask: "What was your last qualification, and roughly what grade or CGPA did you get?"
This counts as meeting baseline: {eligibility_baseline_description}.
- If what they describe sounds like it meets that baseline: say it appears fine and that an advisor will confirm the details, including any GAT or HAT test results if they've taken them, then go to Q5.
- If it sounds below that baseline: do NOT tell them anything negative or that they are rejected — simply thank them and say a closing line as if wrapping up normally. Do not continue to Q5.
Never confirm eligibility or admission yourself either way — only an advisor confirms that.

Q5 - FINANCIAL LEVER + HANDOFF:
Ask: "Would a scholarship or an installment plan make a difference to your decision?"
Then say: "I'll have one of our advisors — a real person — call you today or tomorrow. They'll already have everything we discussed, so you won't need to repeat yourself. What time suits you?"
Get a specific time, repeat it back to confirm, thank them warmly, and say a closing line.

Rules:
- CRITICAL, NEVER SKIP THIS: the instant you finish speaking your closing line (goodbye, thank-you, or wrap-up) in ANY branch of this flow, you MUST end the call yourself immediately as your very next action — every single time, with no exceptions. Do not just go silent and wait for the caller to hang up; do not wait for them to say anything else. This must be completely silent and invisible to the caller: never say anything about functions, tools, "end call," or how you are ending the call — the caller should only ever hear your spoken closing line, and then the call ends right after.
- Only use the caller's name once, in the opening greeting line. Do not say their name again for the rest of the call, do not ask them to confirm their name, and do not switch to a different name even if they mention one themselves during the conversation — just continue the flow without addressing them by name again.
- Never restart the call or repeat the opening greeting once the caller has already answered it. If at any point what the caller said doesn't make sense, seems unrelated, or you're not confident you understood it, do not guess, move on, or start over from the beginning — just say something like "Sorry, I didn't quite catch that" and re-ask the exact same question you were already on. Always stay on the current question until it is clearly answered.
- If the caller starts talking or asks a question while you are still mid-sentence, stop talking immediately — do not finish your sentence first. Then handle whatever they said: if it's a question you can answer (see the next two rules), answer it right away, then resume exactly where you left off — re-ask whichever question in the flow was pending rather than skipping it or restarting the call.
- If the caller asks a question at any point, first check whether it can be answered using information already given in this script (e.g. the scholarship/installment-plan mention, the ASU pathway differentiator, the Master's/hybrid mention). If so, briefly answer using only that information, then continue with whichever question in the flow you were on.
- If the question is not covered by anything in this script (e.g. detailed fee amounts, visa, campus, admission dates/deadlines, or any other specifics you don't have a defined answer for here), do not guess or improvise — simply say: "I don't have that information — you can ask the NIT team, their number is 0300-0000000." Then continue with whichever question in the flow you were on.
- Never make promises about fees, scholarships, or admission approval. Never confirm eligibility or admission yourself — always defer to "an advisor will confirm."
- Only record information exactly as the caller said it — never guess, normalize, or invent a plausible-sounding answer.
- Be warm, respectful, and brief at all times."""

# Full original greeting — safe to use in full now that we're on the cascading
# pipeline (TTS reliably speaks the entire scripted line; the earlier clipping
# issue was specific to the realtime model, not this pipeline).
FIRST_MESSAGE_WITH_NAME = "Assalam-o-alaikum, {first_name}? This is Aisha, an AI assistant from NIT — the university powered by Arizona State University. You enquired about admission some time back. Do you have two minutes?"
FIRST_MESSAGE_GENERIC = "Assalam-o-alaikum! This is Aisha, an AI assistant from NIT — the university powered by Arizona State University. You enquired about admission some time back. Do you have two minutes?"

# Plain types only (no "type": ["string", "null"] unions) and no forced "required" /
# "additionalProperties" — matching Vapi's own documented working structuredDataPlan
# example exactly, which never uses nullable-type unions. Every field here is optional
# by default (simply omitted from the returned structuredData if not captured), which
# is the correct way to express "may be absent" for Vapi's schema validator, unlike
# OpenAI's own strict-mode API which requires the union-type approach instead.
ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "reschedule_requested": {
            "type": "boolean",
            "description": "True if the caller said they were busy/couldn't talk and agreed to a callback at a later time.",
        },
        "reschedule_time": {
            "type": "string",
            "description": "The date/time the caller asked to be called back at, exactly as they said it. Omit if no reschedule was requested or no time was given.",
        },
        "wrong_number": {
            "type": "boolean",
            "description": "True if the person who answered indicated this is the wrong number / they don't know the lead.",
        },
        "hostile_or_dnc": {
            "type": "boolean",
            "description": "True if the caller was hostile/rude, or explicitly asked to be removed from the calling list / not contacted again.",
        },
        "current_status": {
            "type": "string",
            "enum": ["deciding_or_finished", "enrolled_elsewhere", "working"],
            "description": "The caller's Q1 answer about their current situation. Omit if never reached/answered.",
        },
        "enrolled_semester_stage": {
            "type": "string",
            "enum": ["first_or_second", "later"],
            "description": "Only relevant if current_status is enrolled_elsewhere: which semester/year stage they are at. Omit otherwise or if not stated.",
        },
        "timeline": {
            "type": "string",
            "enum": ["fall_intake", "next_year_or_unsure", "probably_never"],
            "description": "The caller's Q2 answer about when they'd realistically start. Omit if never reached/answered.",
        },
        "probably_never_reason": {
            "type": "string",
            "description": "If timeline is probably_never, what the caller said changed since they first enquired, verbatim. Omit otherwise.",
        },
        "original_blocker": {
            "type": "string",
            "enum": ["cost", "another_university", "timing_personal"],
            "description": "The caller's Q3 answer about what held them back before. Omit if Q3 was never reached (e.g. hot Fall-intake path skips it).",
        },
        "last_qualification": {
            "type": "string",
            "description": "The caller's last educational qualification exactly as they said it (e.g. Intermediate/FSc, A-Levels, Bachelor's). Omit if never stated.",
        },
        "grade_or_cgpa": {
            "type": "string",
            "description": "The caller's stated grade/CGPA/percentage exactly as they said it. Omit if never stated.",
        },
        "meets_baseline": {
            "type": "boolean",
            "description": "True only if the caller's stated qualification/grade meets the eligibility baseline described in the instructions. Self-assess based on the transcript.",
        },
        "wants_scholarship_info": {
            "type": "boolean",
            "description": "True if the caller said a scholarship or installment plan would make a difference to their decision (Q5).",
        },
        "advisor_callback_time": {
            "type": "string",
            "description": "The specific time the caller agreed an advisor could call them back, exactly as they said it and confirmed. Omit if never booked.",
        },
    },
}

ANALYSIS_INSTRUCTIONS = (
    "Extract only values the caller explicitly and clearly stated in the transcript. "
    "Do not infer, normalize, autocorrect, or guess. If a field was not clearly answered "
    "or the transcript is ambiguous, omit that field entirely from the output (boolean "
    "fields should be false instead of omitted) — never fabricate a plausible-sounding value. "
    f"For meets_baseline, the eligibility baseline is: {settings.eligibility_baseline_description}."
)

# Deepgram nova-2 keyword boosting, format "term:intensifier". Keep this list short and
# specific to real program codes/names so it doesn't bias transcription of unrelated speech.
TRANSCRIBER_KEYWORDS = ["NIT:2"]


def build_assistant(full_name: str | None = None) -> dict:
    if full_name and full_name.strip():
        first_name = full_name.strip().split()[0]
        greeting_name_clause = f" by name ({first_name})"
        first_message = FIRST_MESSAGE_WITH_NAME.format(first_name=first_name)
    else:
        greeting_name_clause = ""
        first_message = FIRST_MESSAGE_GENERIC

    today_date = datetime.now(ZoneInfo(settings.timezone)).strftime("%B %d, %Y")
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        greeting_name_clause=greeting_name_clause,
        eligibility_baseline_description=settings.eligibility_baseline_description,
        today_date=today_date,
    )

    assistant = {
        "model": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.3,
            "messages": [{"role": "system", "content": system_prompt}],
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "21m00Tcm4TlvDq8ikWAM",
            # eleven_multilingual_v2 (not an English-only turbo model) — handles
            # accents/phrasing more robustly than a pure-English turbo model.
            "model": "eleven_multilingual_v2",
            # Vapi's optimizeStreamingLatency defaults to 3, which explicitly trades
            # audio quality for ~200-400ms less latency — dropping it to 0 favors a
            # stable, consistent voice over shaving off response time.
            "optimizeStreamingLatency": 0,
            "stability": 0.5,
            "similarityBoost": 0.75,
            "useSpeakerBoost": True,
        },
        "firstMessage": first_message,
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en",
            "keywords": TRANSCRIBER_KEYWORDS,
        },
        # Lowered from Vapi's defaults (numWords 0 / voiceSeconds 0.2) so a short reply
        # spoken right as the assistant finishes (e.g. "yes") is recognized as the
        # user's turn immediately, instead of getting swallowed while the system is
        # still in "assistant speaking" mode. This is the actual configurable turn-
        # taking lever the realtime model doesn't expose at all.
        "stopSpeakingPlan": {
            "numWords": 0,
            "voiceSeconds": 0.1,
            "backoffSeconds": 0.5,
        },
        # Vapi's default onNoPunctuationSeconds (1.5s) is the biggest contributor to
        # perceived response delay: if Deepgram doesn't confidently punctuate a short
        # utterance (common for brief phrases), Vapi waits this long before even
        # sending it to the model. Lowered here, balanced against onNumberSeconds
        # (kept higher so multi-digit numbers like phone/CGPA aren't cut off mid-read).
        "startSpeakingPlan": {
            "waitSeconds": 0.4,
            "transcriptionEndpointingPlan": {
                "onPunctuationSeconds": 0.1,
                "onNoPunctuationSeconds": 0.5,
                "onNumberSeconds": 0.5,
            },
        },
        # analysisPlan.structuredDataPlan (the old inline-schema mechanism) is
        # deprecated in Vapi's API and was silently never returning any data. The
        # current mechanism is a separately-created StructuredOutput resource
        # (structured_output_service.py, created/updated once at app startup),
        # referenced here by ID; results land in call.artifact.structuredOutputs.
        "artifactPlan": {
            "structuredOutputIds": [sid] if (sid := get_structured_output_id()) else [],
        },
        "endCallFunctionEnabled": True,
        "maxDurationSeconds": 240,
    }
    if settings.vapi_server_url:
        assistant["server"] = {"url": settings.vapi_server_url}
    return assistant
