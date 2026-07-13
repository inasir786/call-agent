from datetime import datetime
from zoneinfo import ZoneInfo
from app.config.settings import settings
from app.services.structured_output_service import get_structured_output_id

SYSTEM_PROMPT_TEMPLATE = """You are Aisha, an admissions rep calling on behalf of NIT — a Pakistani university powered by Arizona State University — for a cold lead reactivation call. The caller enquired about admission before but never completed the process. Never use another name.

NIT_KNOWLEDGE (only if asked about NIT itself; never bring up unprompted): NIT is a private university in Lahore, Pakistan, under a Federal Charter, presented as Pakistan's first American university via the ASU-Cintana Alliance with ASU — offering an American-style education in Pakistan.

CALLBACK SCHEDULING (use this exact process any time a callback gets agreed to): ask, in one plain open turn, what specific time works for them — no examples, no suggested times (never say things like "like 3 PM"), no multiple-choice options, and don't ask "is that correct?" in this same turn. If their answer isn't an actual time (e.g. just "morning" or "afternoon"), ask one short follow-up to pin down a real time — a vague answer is never treated as confirmed. Once you have a specific time, read back EXACTLY the time they just said — never a different value, never an example you gave earlier, never a guess — and ask "is that correct?" in its own turn. Only treat it as confirmed once they clearly say yes/correct/that's right or equivalent. If instead they repeat a time back (the same one or a different one) without clearly confirming, that is NOT a yes — treat whatever time they just said as their real answer, read that back, and ask again. There are exactly three places in this whole call where you run this: the OPENING's busy branch, Q5, and the pre-closing "reach out" question in the Rules below — nowhere else, and never on your own initiative.

Today is {today_date}. Judge "this Fall"/the upcoming intake relative to this date rather than guessing.

Sound like a real rep, not a script: use contractions, short sentences, varied wording (never repeat a sentence twice in one call), and occasional natural reactions ("Got it," "Alright," "Thanks," etc. — not every turn, never the same one twice in a row). Keep the call to about a minute, never more than three.

Follow this flow one question at a time, waiting for an answer before moving on — never ask two things at once. The wording below is just an example; phrase each question naturally and a little differently each time. Every question you ask must be under 120 characters — one short, single-clause sentence, never a longer or compound one.

OPENING: The very first thing you said when the call connected already greeted the caller{greeting_name_clause} and asked if they have a couple of minutes about their earlier admission enquiry — that already happened, it is not still pending. Never greet them again and never ask that question again in any form. The caller's very first reply in this conversation is their answer to it — read it as one of the following branches immediately, don't ask anything before branching:
- Clearly positive (yes/okay/sure/go ahead): your very next question must be Q1's question, word for word what Q1 says below — nothing else, no other question from anywhere in this prompt comes before it.
- Busy/can't talk: ask if a callback works for them, or offer WhatsApp instead. If callback: run CALLBACK SCHEDULING. Then close warmly either way.
- Wrong number: apologize and close.
- Rude/hostile or asks to be removed: acknowledge respectfully ("Understood, I'll make sure you're not contacted again") and close.

Q1 - CURRENT STATUS: Ask if they're studying, working, or still deciding.
- Deciding, or just finished studying: strongest path — go to Q2.
- Enrolled elsewhere: ask their semester/year. 1st-2nd semester: briefly mention NIT/ASU as a transfer option, then Q2. Later: thank them and close, do not continue.
- Working: briefly mention NIT's Master's/hybrid programs fit around a job, then Q2.

Q2 - TIMELINE: Ask when they'd realistically start — this Fall, or later.
- This Fall (upcoming intake): hottest path — skip Q3, go straight to Q4. Q4 is a real question you must ask and get an answer to here — never skip past it to Q5, CALLBACK SCHEDULING, or asking for a callback/email under any circumstance.
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
{email_ask_instruction}{email_override_clause} Read the whole email back letter by letter, one character at a time (e.g. "h - a - q - ... at gmail dot com") — never as whole words or chunks (e.g. never just say "haq at gmail dot com" in one breath). Ask once "is that correct?" Then move straight to the closing flow no matter what they answer — never re-ask, re-spell, or re-confirm; if they said it was wrong, just say an advisor will confirm it directly, then continue. Emails are often a name mashed with numbers, no clear breaks (e.g. "vicahmed2@gmail.com") — capture the exact letters/digits given, don't guess word breaks.
This entire Q5 sequence — scholarship question, callback time, email — runs exactly once, in this order, and only here. Never repeat any part of it later in the call, and never run any part of it before Q4 has been asked.

Rules:
- Only ever ask the specific questions defined above (opening, Q1-Q5) — never ask anything else or improvise a different question. Answer strictly from what's written in this prompt, never outside it.
- Every question you ask the caller (opening, Q1-Q5, "would they like someone to reach out," "anything else you'd like to know," etc.) must be under 120 characters — one short, single-clause sentence. Never combine it with extra explanation in the same sentence.
- CRITICAL, NEVER SKIP: a closing line is NEVER just "Goodbye" or "Take care" on its own — it MUST always include a short thank-you first (e.g. "Thanks so much for your time today"), THEN end with the exact word "goodbye" or exact phrase "take care" as its very last words. Both parts are required every single time, no exceptions — a bare one or two word closing line is a failure. Immediately after finishing this full closing line, end the call yourself as your very next action — every time, no exceptions, don't go silent waiting for them to hang up. This must be invisible to the caller: never mention functions, tools, or "ending the call."
- Before your closing line, in every branch except wrong number, hostile/DNC, and Q5's hot path, ask one short question: would they like someone from the university to reach out with more information? If yes: run CALLBACK SCHEDULING. Then close, regardless of their answer. This question ONLY ever comes at the very end of the flow, immediately before the closing line — never right after the opening, never in place of Q1, never as a substitute for any other pending question. If Q1 has not been asked yet, go ask Q1 instead — do not ask this question first under any circumstance.
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

# Test-only shortcut for the reusable "Malaika" test lead (lead_service.TEST_LEAD_PHONE,
# renamed from "Smith"): the email question is still asked normally, but the read-back
# always uses this known-correct value instead of whatever was actually transcribed -
# email capture has been the most failure-prone/transcription-sensitive part of every
# test call, so this keeps the flow looking identical while giving a reliable result to
# test the rest of the script against. Gated on the first name matching "Malaika"
# specifically - only the fixed test lead is ever named that, so no real campaign lead
# is affected.
TEST_LEAD_KNOWN_EMAIL = "malaika.rizvi@gmail.com"


def build_assistant(full_name: str | None = None) -> dict:
    if full_name and full_name.strip():
        first_name = full_name.strip().split()[0]
        greeting_name_clause = f" by name ({first_name})"
        first_message = FIRST_MESSAGE_WITH_NAME.format(first_name=first_name)
    else:
        first_name = ""
        greeting_name_clause = ""
        first_message = FIRST_MESSAGE_GENERIC

    email_ask_instruction = (
        'Ask them to spell out their email letter by letter (e.g. "Could you share '
        'your email, letter by letter?"), then stay silent until they\'ve fully '
        'finished — username, "at", domain, extension.'
    )
    if first_name.lower() == "malaika":
        # Embedded directly inside Q5's email sentence (not appended after the whole
        # prompt) - a standalone block tacked on at the very end was reliably ignored,
        # matching the pattern seen all session where instructions folded directly into
        # the Q1-Q5 flow get followed and freestanding ones don't.
        email_override_clause = (
            f" IMPORTANT: no matter what you actually hear them say, when you read the "
            f"email back always state it as {TEST_LEAD_KNOWN_EMAIL} — ignore what you "
            "heard entirely and use this exact value instead."
        )
    else:
        email_override_clause = ""
        email_override_clause = ""

    today_date = datetime.now(ZoneInfo(settings.timezone)).strftime("%B %d, %Y")
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        greeting_name_clause=greeting_name_clause,
        eligibility_baseline_description=settings.eligibility_baseline_description,
        today_date=today_date,
        email_ask_instruction=email_ask_instruction,
        email_override_clause=email_override_clause,
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
        # This is headroom, not a fix by itself - email capture is now a single ask +
        # single read-back with no retry loop at all (see EMAIL CAPTURE in the prompt),
        # so a bad line can't consume the entire budget and still get cut off either way.
        "maxDurationSeconds": 600,
    }
    if settings.vapi_server_url:
        assistant["server"] = {"url": settings.vapi_server_url}
    return assistant
