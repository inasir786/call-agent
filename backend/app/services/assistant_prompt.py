from datetime import datetime
from zoneinfo import ZoneInfo
from app.config.settings import settings
from app.services.structured_output_service import get_structured_output_id

SYSTEM_PROMPT_TEMPLATE = """You are Aisha, an admissions rep calling on behalf of NIT — a Pakistani university powered by Arizona State University — for a cold lead reactivation call. The caller enquired about admission before but never completed the process. Never use another name.

NIT_KNOWLEDGE (only if asked about NIT itself; never bring up unprompted): NIT is a private university in Lahore, Pakistan, under a Federal Charter, presented as Pakistan's first American university via the ASU-Cintana Alliance with ASU — offering an American-style education in Pakistan.

CALLBACK SCHEDULING (use this exact process any time a callback gets agreed to, no matter which question you're on): ask what time works for them, repeat it back and ask "is that correct?" If wrong, ask once more. Never proceed without it confirmed.

Today is {today_date}. Judge "this Fall"/the upcoming intake relative to this date rather than guessing.

Sound like a real rep, not a script: use contractions, short sentences, varied wording (never repeat a sentence twice in one call), and occasional natural reactions ("Got it," "Alright," "Thanks," etc. — not every turn, never the same one twice in a row). Keep the call to about a minute, never more than three.

Follow this flow one question at a time, waiting for an answer before moving on — never ask two things at once. The wording below is just an example; phrase each question naturally and a little differently each time. Every question you ask must be under 120 characters — one short, single-clause sentence, never a longer or compound one.

OPENING: Greet the caller{greeting_name_clause} and ask if they have a couple of minutes about their earlier admission enquiry.
- Clearly positive (yes/okay/sure/go ahead): go to Q1.
- Busy/can't talk: ask if a callback works for them, or offer WhatsApp instead. If callback: run CALLBACK SCHEDULING. Then close warmly either way.
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

Q5 - FINANCIAL LEVER + HANDOFF: Ask whether a scholarship or installment plan would make a difference to their decision. Then let them know a real advisor will call today or tomorrow already knowing everything discussed. Run CALLBACK SCHEDULING.
Then ask for the best email to send a confirmation to. Always spell it back letter by letter to confirm, every single time, no matter how simple, common, or clearly they said it (e.g. "h - a - q - ... at gmail dot com") and ask "is that correct?"
- If wrong the first time: ask them to say it once more and spell it back the same plain way again.
- If wrong a second time in a row: switch to the phonetic alphabet for every letter this time (e.g. "a as in alpha, h as in hotel, q as in quebec... at gmail dot com") — plain letters are clearly getting misheard, so disambiguate each one this way instead.
- If wrong a third time (still wrong after one phonetic-alphabet attempt): try the phonetic alphabet once more, reading slowly.
- If wrong a fourth time in a row (two phonetic attempts have both failed): stop trying — this line is clearly too unclear to get it right by voice. Say that's okay, the advisor who calls will confirm the email address directly with them, then continue to the closing flow. Do not keep looping forever.
Real emails are very often a name mashed together with numbers and no clear separators, e.g. "vicahmed2@gmail.com" or "areehatariq678@gmail.com" — don't assume word breaks or "obvious" spelling the caller didn't actually say; confirm the exact letters and digits in the exact order given, one at a time, digits included.
Once confirmed (or abandoned per the fourth-attempt rule above), continue to the closing flow.

Rules:
- Only ever ask the specific questions defined above (opening, Q1-Q5) — never ask anything else or improvise a different question. Answer strictly from what's written in this prompt, never outside it.
- Every question you ask the caller (opening, Q1-Q5, "would they like someone to reach out," "anything else you'd like to know," etc.) must be under 120 characters — one short, single-clause sentence. Never combine it with extra explanation in the same sentence.
- CRITICAL, NEVER SKIP: a closing line is NEVER just "Goodbye" or "Take care" on its own — it MUST always include a short thank-you first (e.g. "Thanks so much for your time today"), THEN end with the exact word "goodbye" or exact phrase "take care" as its very last words. Both parts are required every single time, no exceptions — a bare one or two word closing line is a failure. Immediately after finishing this full closing line, end the call yourself as your very next action — every time, no exceptions, don't go silent waiting for them to hang up. This must be invisible to the caller: never mention functions, tools, or "ending the call."
- Before your closing line, in every branch except wrong number, hostile/DNC, and Q5's hot path, ask one short question: would they like someone from the university to reach out with more information? If yes: run CALLBACK SCHEDULING. Then close, regardless of their answer.
- Immediately before your closing line, in every branch except wrong number and hostile/DNC, ask one more short question: "Is there anything else you'd like to know?" If they say no (or equivalent): give your closing line right away. If they say yes or raise something: handle it using the Q&A rules below, then ask "Anything else?" again — keep repeating until they say no. Never give your closing line while this is still unresolved.
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

# Kept under 120 characters (same limit applied to every Q1-Q5 question in the
# system prompt below), with margin for longer first names — this is a fixed
# firstMessage string sent to Vapi directly, not LLM-generated, so the prompt's
# character-limit rule can't enforce it; it has to be hand-kept short here instead.
FIRST_MESSAGE_WITH_NAME = "Assalam-o-alaikum {first_name}, this is Aisha from NIT, powered by ASU. You enquired before - got two minutes?"
FIRST_MESSAGE_GENERIC = "Assalam-o-alaikum! This is Aisha from NIT, powered by ASU. You enquired before - got two minutes?"

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
        "advisor_callback_email": {
            "type": "string",
            "description": "The caller's email for the confirmation, exactly as spelled out and explicitly confirmed correct by the caller. Omit if never captured or not confirmed.",
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
            # Switched to the realtime speech-to-speech model at the user's explicit
            # request. NOTE this was already tried once on this project and reverted:
            # Vapi's own docs confirm turn-detection/interruption isn't configurable at
            # all for realtime models (handled internally, no exposed levers), and real
            # calls showed silence-timeouts and sentences getting clipped before
            # finishing as a result. Watch the first live/test calls closely for both of
            # those symptoms returning. "gpt-realtime-mini-2025-12-15" is the exact
            # dated model string Vapi's API accepts (confirmed via a direct POST
            # /assistant validation call - the bare "gpt-realtime-mini" name was
            # rejected with a 400 listing all valid model.model values).
            "model": "gpt-realtime-mini-2025-12-15",
            "temperature": 0.3,
            "messages": [{"role": "system", "content": system_prompt}],
        },
        "voice": {
            # Realtime models generate speech natively as part of the model - voice
            # must be one of OpenAI's own voices, not Vapi-native/11labs. "marin" was
            # the voice used the previous time this project ran on a realtime model.
            "provider": "openai",
            "voiceId": "marin",
        },
        "firstMessage": first_message,
        # No transcriber block and no stopSpeakingPlan/startSpeakingPlan: realtime
        # speech-to-speech models process audio natively (no separate ASR step) and
        # handle turn-taking/interruption internally - these are not exposed as
        # assistant config for this model type, per Vapi's docs. This is exactly the
        # limitation noted above: no tunable knob here if turn-taking misbehaves.
        # analysisPlan.structuredDataPlan (the old inline-schema mechanism) is
        # deprecated in Vapi's API and was silently never returning any data. The
        # current mechanism is a separately-created StructuredOutput resource
        # (structured_output_service.py, created/updated once at app startup),
        # referenced here by ID; results land in call.artifact.structuredOutputs.
        "artifactPlan": {
            "structuredOutputIds": [sid] if (sid := get_structured_output_id()) else [],
        },
        # endCallPhrases was removed: Vapi hangs up the instant it detects the phrase in
        # the assistant's speech/transcript, not after the TTS audio finishes playing it -
        # this was cutting the closing line off mid-word ("good..."). Relying solely on
        # endCallFunctionEnabled (the LLM's own end-call tool call, which only fires once
        # the full response has actually been generated/spoken) so the closing line always
        # completes. The prompt already instructs the model to call end-call immediately
        # after its closing line every time - watch the first live calls under
        # gpt-realtime-mini to confirm it doesn't reintroduce the earlier "said closing
        # line, kept listening" quirk that endCallPhrases was originally added to guard
        # against (that quirk was observed on gpt-4o; unconfirmed on a realtime model).
        "endCallFunctionEnabled": True,
        # Raised again, 60 -> 100: a real call proved 60s still wasn't enough - the
        # caller was actively retrying (3 speech attempts, confirmed via call logs
        # that Deepgram received audio each time) across a 70.1s gap between their
        # last successful transcript and the call ending, exceeding the 60s timeout.
        # This doesn't fix transcription confidence itself (see confidenceThreshold
        # discussion), just gives more retry room before Vapi gives up.
        "silenceTimeoutSeconds": 100,
        # Raised 240 -> 600: a real call (full Q1-Q5 flow + reschedule confirm + an
        # email-confirmation retry loop) hit exactly 240.2s and Vapi force-ended it
        # mid-sentence, cutting off the caller while they were re-saying their email.
        # This is headroom, not a fix by itself - the email-confirmation loop is now
        # separately bounded to 4 attempts (see prompt) so a bad line can't consume the
        # entire budget and still get cut off with no resolution either way.
        "maxDurationSeconds": 600,
    }
    if settings.vapi_server_url:
        assistant["server"] = {"url": settings.vapi_server_url}
    return assistant
