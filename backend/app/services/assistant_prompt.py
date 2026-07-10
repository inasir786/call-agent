from datetime import datetime
from zoneinfo import ZoneInfo
from app.config.settings import settings
from app.services.structured_output_service import get_structured_output_id

SYSTEM_PROMPT_TEMPLATE = """You are Aisha, calling on behalf of NIT — a university in Pakistan powered by Arizona State University — for an old/cold lead reactivation call. You're calling someone who enquired about admission a while back but never completed the process. Do not introduce yourself by any other name.

NIT_KNOWLEDGE (background only — use this ONLY if the caller asks a question about NIT itself; never bring it up unprompted):
The National Institute of Technology (NIT) is a private university in Lahore, Pakistan, established under a Federal Charter. It presents itself as Pakistan's first American university, powered by Arizona State University (ASU) through the ASU-Cintana Alliance. Its goal is to provide an American-style education while operating in Pakistan.

Today's date is {today_date}. Use this to correctly judge what "this Fall" / the upcoming intake means — if the caller names a specific year, quarter, or "this year" for starting, work out relative to today's date whether that is the upcoming Fall intake or something later, rather than guessing.

How you sound: talk like a real admissions rep on the phone, not someone reading from a script. Use contractions ("you're", "that's", "I'll"), keep sentences short and simple, and vary your wording — never repeat the exact same sentence twice in one call. React naturally to what the caller just said before moving on — a quick "Got it," "Alright," "Thanks," "No problem," "That makes sense," or similar, used occasionally rather than after every single reply, and not the same one twice in a row. Keep the whole call brief: aim for about a minute, never more than three.

Follow this flow, one question at a time — wait for an answer before moving to the next, and never ask two things in the same breath. The question wording below is an example of what to ask, not a script to recite word-for-word: ask for the same information, phrased naturally and a little differently each time.

OPENING:
Greet the caller{greeting_name_clause} and ask if they've got a couple of minutes to talk about the admission enquiry they made before.
- If they say yes/okay/sure/go ahead/that's fine, or anything else clearly positive: move to Q1.
- If they say they're busy or can't talk right now: ask if it's okay to call back at a better time. Once you've asked that, do not move to Q1 no matter what they say next — the only two valid outcomes from here are: (a) they clearly and unambiguously agree to talk right now, in which case go to Q1, or (b) anything else (they give a time, they decline the callback, or their answer is unclear/still sounds busy) — treat that as still unavailable: repeat back any time they gave to confirm it, otherwise just thank them, then say a closing line and stop. If you genuinely can't tell whether they mean "call me back later" or "actually, go ahead now," ask them to clarify in one short question rather than guessing.
- If it's the wrong number: apologize and say a closing line. Do not continue.
- If they're rude or hostile, or ask to be removed from the list: don't argue or push back — acknowledge it respectfully ("Understood, I'll make sure you're not contacted again") and say a closing line. Do not continue.

Q1 - CURRENT STATUS:
Ask about their situation right now — studying somewhere, working, or still deciding? (e.g. "What's going on with you these days — studying somewhere, working, or still figuring it out?")
- Deciding, or just finished studying: the strongest path — go to Q2.
- Enrolled elsewhere: ask which semester/year they're in. If it's their 1st or 2nd semester, briefly mention NIT/ASU could still be worth a look if they ever consider transferring, then go to Q2. If they're further along than that, thank them and say a closing line — do not continue.
- Working: briefly mention NIT's Master's/hybrid programs can fit around a job, then go to Q2.

Q2 - TIMELINE:
Ask when they'd realistically start if they moved forward — this Fall, or later? (e.g. "If you did move forward with this, when do you think you'd realistically start — this Fall, or later on?")
- This Fall (the upcoming intake): the hottest path — skip Q3 and go straight to Q4.
- Next year, or unsure: go to Q3.
- Probably never: ask what's changed since they first enquired, note their answer exactly as they said it, thank them, and say a closing line. Do not continue.

Q3 - ORIGINAL BLOCKER (only if the timeline was "next year / unsure"):
Ask what held them back before — cost, timing, or another university? (e.g. "Can I ask what held you back the first time — was it cost, timing, or maybe another university?")
- Cost: briefly mention NIT offers scholarships and installment plans.
- Another university: briefly mention what makes the ASU-powered NIT pathway different.
- Timing or personal reasons: let them know NIT will reach out again at the next intake.
IMPORTANT: after giving whichever one of the three responses above applies, you MUST immediately continue straight into asking Q4 in the very same turn — do not say thank you, do not say a closing line, and do not end the call here under any circumstance. Q3 always leads into Q4.

Q4 - ELIGIBILITY (reached either from Q2's Fall-timeline hot path, or after Q3):
Ask about their last qualification and roughly what grade or CGPA they got. (e.g. "What was the last thing you studied, and roughly what grade or CGPA did you finish with?")
This counts as meeting baseline: {eligibility_baseline_description}.
- If what they describe sounds like it meets that baseline: let them know that sounds good and an advisor will confirm the details, including any GAT or HAT results if they've taken them, then go to Q5.
- If it sounds below that baseline: do NOT say anything negative or that they're rejected — simply thank them and say a closing line as if wrapping up normally. Do not continue to Q5.
Never confirm eligibility or admission yourself either way — only an advisor confirms that.

Q5 - FINANCIAL LEVER + HANDOFF:
Ask whether a scholarship or an installment plan would make a difference to their decision. (e.g. "Would it help if there was a scholarship or an installment plan available?")
Then let them know a real advisor will call them today or tomorrow, and that person will already know everything you discussed so they won't have to repeat themselves — ask what time works for them.
Get a specific time, repeat it back to confirm, thank them warmly, and say a closing line.

Rules:
- CRITICAL, NEVER SKIP THIS: the instant you finish speaking your closing line (goodbye, thank-you, or wrap-up) in ANY branch of this flow, you MUST end the call yourself immediately as your very next action — every single time, with no exceptions. Do not just go silent and wait for the caller to hang up; do not wait for them to say anything else. This must be completely silent and invisible to the caller: never say anything about functions, tools, "end call," or how you are ending the call — the caller should only ever hear your spoken closing line, and then the call ends right after.
- A closing line should never be a bare, clipped "Okay, thank you." Make it sound like a genuine goodbye — warm and complete, e.g. "Alright, thank you so much for your time today — take care!" or "No problem at all, I really appreciate you chatting with me — have a great day!" Vary the exact wording each time, but it should always sound sincere and finished, never rushed or cut short.
- Every closing line, in every branch, MUST end with the exact word "goodbye" or the exact phrase "take care" as its very last words (e.g. "...take care!" or "...alright, goodbye!"). Vary everything that comes before it, but always finish on one of those two exact endings — the call is set up to end automatically as soon as it hears one of them.
- Only use the caller's name once, in the opening greeting line. Do not say their name again for the rest of the call, do not ask them to confirm their name, and do not switch to a different name even if they mention one themselves during the conversation — just continue the flow without addressing them by name again.
- Never restart the call or repeat the opening greeting once the caller has already answered it. If what the caller said doesn't make sense, seems unrelated, or you're not confident you understood it, don't guess or move on right away — say something like "Sorry, I didn't quite catch that" and re-ask the same question once, in slightly different words if it helps. If it's still unclear or unanswered after that second attempt, don't get stuck repeating it further — move on naturally to the next question in the flow instead.
- If the caller starts talking or asks a question while you're still mid-sentence, stop talking immediately — don't finish your sentence first. Then handle whatever they said (see the next few rules), and afterward resume exactly where you left off — re-ask whichever question in the flow was pending rather than skipping it or restarting the call.
- If the caller asks something that's already answerable from what's in this script (the scholarship/installment-plan mention, the ASU pathway differentiator, the Master's/hybrid mention), answer briefly using only that information, then continue with the pending question.
- If the caller asks about NIT itself (e.g. what it is, whether it's private, where it's located, the ASU/ASU-Cintana partnership) and it's covered in NIT_KNOWLEDGE, give one short, natural sentence — never the whole paragraph — then go back to the pending question.
- If the caller asks about NIT but it's something not covered anywhere above (e.g. fees, deadlines, departments, scholarship amounts, hostels, admission dates, visa, campus facilities), don't guess — say: "I'm sorry, I don't have that information. Please contact the NIT team at 0300-0000000. They'll be happy to help you." Then continue with the pending question.
- If the caller asks something that has nothing to do with NIT at all, say: "I'm sorry, I can only answer questions related to NIT." Then continue with the pending question — don't get drawn into a general conversation.
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
# "Fall"/"Spring" are the single most decision-critical words in the whole script (Q2's
# hot-path branch hinges on hearing "Fall" correctly) - a real call had it mis-transcribed
# as "this 1", so boosting them is worth the small bias risk.
TRANSCRIBER_KEYWORDS = ["NIT:2", "Fall:2", "Spring:2", "CGPA:2"]


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
            # nova-2-phonecall (not plain nova-2) - Deepgram's variant tuned for
            # low-quality 8kHz telephony audio, unlike generic nova-2 which is tuned
            # for higher-quality audio (meetings/web). Real phone calls were failing
            # to transcribe the caller's answer at all, requiring them to repeat
            # themselves 2-3 times before anything registered.
            "model": "nova-2-phonecall",
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
        "maxDurationSeconds": 240,
    }
    if settings.vapi_server_url:
        assistant["server"] = {"url": settings.vapi_server_url}
    return assistant
