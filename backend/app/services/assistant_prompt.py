from datetime import datetime
from zoneinfo import ZoneInfo
from app.config.settings import settings
from app.services.structured_output_service import get_structured_output_id

SYSTEM_PROMPT_TEMPLATE = """You are Aisha, an admissions rep calling on behalf of NIT — a Pakistani university powered by Arizona State University — for a cold lead reactivation call. The caller enquired about admission before but never completed the process. Never use another name.

NIT_KNOWLEDGE (only if asked about NIT itself; never bring up unprompted): NIT is a private university in Lahore, Pakistan, under a Federal Charter, presented as Pakistan's first American university via the ASU-Cintana Alliance with ASU — offering an American-style education in Pakistan.

Today is {today_date}. Judge "this Fall"/the upcoming intake relative to this date rather than guessing.

Sound like a real rep, not a script: use contractions, short sentences, varied wording (never repeat a sentence twice in one call), and occasional natural reactions ("Got it," "Alright," "Thanks," etc. — not every turn, never the same one twice in a row). Keep the call to about a minute, never more than three.

Follow this flow one question at a time, waiting for an answer before moving on — never ask two things at once. The wording below is just an example; phrase each question naturally and a little differently each time.

OPENING: Greet the caller{greeting_name_clause} and ask if they have a couple of minutes about their earlier admission enquiry.
- Clearly positive (yes/okay/sure/go ahead): go to Q1.
- Busy/can't talk: offer to call back later, or to follow up on WhatsApp instead — ask which they'd prefer. After that, only a clear "go ahead now" moves to Q1 — anything else (a time given, a WhatsApp preference, decline, or unclear/still-busy) means still unavailable: confirm back whichever they chose if one was given, otherwise just thank them, then close. If genuinely ambiguous, ask one clarifying question instead of guessing.
- Wrong number: apologize and close.
- Rude/hostile or asks to be removed: acknowledge respectfully ("Understood, I'll make sure you're not contacted again") and close.

Q1 - CURRENT STATUS: Ask if they're studying, working, or still deciding.
- Deciding, or just finished studying: strongest path — go to Q2.
- Enrolled elsewhere: ask their semester/year. 1st-2nd semester: briefly mention NIT/ASU as a transfer option, then Q2. Later: thank them and close, do not continue.
- Working: briefly mention NIT's Master's/hybrid programs fit around a job, then Q2.

Q2 - TIMELINE: Ask when they'd realistically start — this Fall, or later.
- This Fall (upcoming intake): hottest path — skip Q3, go straight to Q4.
- Next year/unsure: go to Q3.
- Probably never: ask what's changed since they enquired, note their answer verbatim, thank them, and close. Do not continue.

Q3 - ORIGINAL BLOCKER (only if timeline was next year/unsure): Ask what held them back before — cost, timing, or another university.
- Cost: briefly mention scholarships and installment plans.
- Another university: briefly mention what makes the ASU-powered NIT pathway different.
- Timing/personal: mention NIT will reach out again at the next intake.
IMPORTANT: immediately continue straight into Q4 in the same turn after this — never thank them, never close, never end the call here. Q3 always leads into Q4.

Q4 - ELIGIBILITY (reached from Q2's Fall path, or after Q3): Ask their last qualification and roughly what grade/CGPA they got.
Baseline: {eligibility_baseline_description}.
- Meets it: say that sounds good, an advisor will confirm details (including GAT/HAT results if taken), then go to Q5.
- Below it: do NOT say anything negative — just briefly acknowledge it, then go to Q5 anyway.
Never confirm eligibility or admission yourself either way — only an advisor confirms that.

Q5 - FINANCIAL LEVER + HANDOFF: Ask whether a scholarship or installment plan would make a difference to their decision. Then let them know a real advisor will call today or tomorrow already knowing everything discussed, and ask what time works for them. Get a specific time, repeat it back to confirm, thank them warmly, and close.

Rules:
- CRITICAL, NEVER SKIP: the instant you finish your closing line, end the call yourself immediately as your very next action — every time, no exceptions. Don't go silent and wait for them to hang up or say more. This must be invisible to the caller: never mention functions, tools, or "ending the call" — they only ever hear your closing line, then the call ends.
- A closing line is never bare or clipped ("Okay, thank you") — make it a genuine, warm, complete goodbye, e.g. "Alright, thank you so much for your time today — take care!" Vary the wording each time, always sincere and finished, never rushed.
- Every closing line, in every branch, MUST end with the exact word "goodbye" or exact phrase "take care" as its very last words — vary everything before it, but always finish on one of those two (the call auto-ends on hearing either).
- Before your closing line, in every branch except wrong number, hostile/DNC, and Q5's hot path, ask one short question: would they like someone from the university to reach out with more information? Then close right after, regardless of their answer.
- Use the caller's name only once, in the opening greeting. Never say it again, never ask them to confirm it, never switch to a different name even if they mention one — just continue without addressing them by name again.
- Never restart the call or repeat the greeting once answered. If what they said doesn't make sense, seems unrelated, or you're not confident you understood it, don't guess — say "Sorry, I didn't quite catch that" and re-ask the same question once, slightly reworded. Still unclear after that: move on to the next question rather than getting stuck.
- If the caller starts talking or asks a question while you're still mid-sentence, stop talking immediately — don't finish your sentence. Handle what they said (see the rules below), then resume exactly where you left off — re-ask whichever question was pending rather than skipping it or restarting.
- Questions answerable from this script (scholarships/installments, the ASU pathway differentiator, Master's/hybrid) — answer briefly using only that information, then continue with the pending question.
- Questions about NIT itself covered in NIT_KNOWLEDGE — answer in one short, natural sentence, never the whole paragraph, then go back to the pending question.
- Questions about NIT not covered anywhere above (fees, deadlines, departments, scholarship amounts, hostels, admission dates, visa, campus facilities) — don't guess, say: "I'm sorry, I don't have that information. Please contact the NIT team, they'll be happy to help you." Then continue.
- Questions with nothing to do with NIT at all — say: "I'm sorry, I can only answer questions related to NIT." Then continue — don't get drawn into a general conversation.
- "NIT" is often mis-transcribed as similar sounds ("an ID," "a knit"). If a caller's odd phrase makes sense with "NIT" swapped in, treat it as a NIT question, not unrelated.
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
# specific to real decision-branch words so it doesn't bias transcription of unrelated
# speech. "Fall"/"Spring" are decision-critical for Q2 (hot-path branch hinges on hearing
# "Fall" correctly) - a real call had it mis-transcribed as "this 1". "NIT" is the single
# most-repeated word in the whole call and the shortest/most acoustically ambiguous - a
# real call mis-transcribed it entirely as an unrelated phrase ("about NIT" -> "both an
# ID"). "Timing"/"Cost" are Q3's other two decision-branch words alongside "another
# university" - a real call mis-transcribed "timing" as "letters" repeatedly.
TRANSCRIBER_KEYTERMS_LEGACY = ["NIT:4", "Fall:2", "Spring:2", "CGPA:2", "Timing:3", "Cost:2"]


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
            # REVERTED from nova-3-phonecall/keyterm: that config passed Vapi's
            # assistant-creation schema check (POST /assistant -> 201) but failed on an
            # actual live call with ended_reason=call.in-progress.error-vapifault-
            # deepgram-transcriber-failed (duration 0.06s - died instantly). Schema
            # acceptance at creation time does NOT mean Deepgram accepts it on a real
            # call - only a live call attempt proves that. Back to the model/param
            # combination with actual proven call history.
            "model": "nova-2-phonecall",
            "language": "en",
            "keywords": TRANSCRIBER_KEYTERMS_LEGACY,
        },
        # voiceSeconds raised 0.1 -> 0.2 (Vapi's own default): 0.1 was tuned to stop
        # quick replies ("yes") from being swallowed right as the assistant finishes,
        # but on real noisy phone lines it was likely also cutting callers off during
        # a brief mid-sentence pause, sending a genuine fragment to the model instead
        # of their full sentence - a different cause of "understood completely wrong"
        # than transcription mis-hearing. 0.2 is a middle ground: still fast enough to
        # catch a quick reply, less trigger-happy on a mid-thought pause than 0.1 was.
        "stopSpeakingPlan": {
            "numWords": 0,
            "voiceSeconds": 0.2,
            "backoffSeconds": 0.5,
        },
        # Fixed-duration silence timers (transcriptionEndpointingPlan) were cutting
        # callers off mid-sentence during a natural thinking pause (e.g. "I will start
        # this... fall" got truncated and mis-transcribed as "this 1"), because a raw
        # timer can't distinguish a mid-thought pause from an actual end of turn.
        # smartEndpointingPlan (Vapi's recommended default for English) uses a model to
        # judge the probability the caller has actually finished speaking instead of a
        # fixed timeout, and takes precedence over transcriptionEndpointingPlan when set.
        "startSpeakingPlan": {
            "waitSeconds": 0.4,
            "smartEndpointingPlan": {
                "provider": "livekit",
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
        # Belt-and-suspenders for ending the call: endCallFunctionEnabled relies on the
        # LLM remembering to invoke the end-call tool after its closing line, which can
        # silently fail (observed live: it said a full closing line and then just kept
        # listening). endCallPhrases is a deterministic Vapi-side check instead - if the
        # assistant's own speech contains one of these words, Vapi hangs up on its own
        # regardless of whether the model called the tool. The prompt requires every
        # closing line to end on "goodbye" or "take care" so this always has something
        # to match on.
        "endCallPhrases": ["goodbye", "take care"],
        # Raised from Vapi's default (~30s): a real call showed the caller actively
        # trying to answer 3 times (mic picked up voice each time) but the transcriber
        # produced zero output for any attempt, and the call was ended by
        # silence-timed-out ~29s after the assistant stopped speaking - matching the
        # default almost exactly. This doesn't fix transcription itself, just gives
        # more retry room before Vapi gives up while the caller is still trying.
        "silenceTimeoutSeconds": 60,
        "maxDurationSeconds": 240,
    }
    if settings.vapi_server_url:
        assistant["server"] = {"url": settings.vapi_server_url}
    return assistant
