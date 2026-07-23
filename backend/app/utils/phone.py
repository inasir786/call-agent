import re

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def normalize_phone(raw: str) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return None
    if digits.startswith("00"):
        digits = digits[2:]
    # Bare Pakistani mobile entered without a country code, e.g. "03001234567" or "3001234567"
    if len(digits) == 11 and digits.startswith("03"):
        return f"+92{digits[1:]}"
    if len(digits) == 10 and digits.startswith("3"):
        return f"+92{digits}"
    # Any other number already carrying its own country code (E.164 allows 8-15 digits)
    if 8 <= len(digits) <= 15:
        return f"+{digits}"
    return None


# Backwards-compatible alias — kept for any lingering imports.
normalize_pk_phone = normalize_phone


def is_valid_email(value: str | None) -> bool:
    if not value:
        return False
    return bool(EMAIL_RE.match(value.strip()))


# Spoken-word substitutions for emails that arrive as transcribed speech
# ("malaika dot rizvi at gmail dot com"). Surrounding spaces are required so
# letters inside names ("fatima") are never touched. "at the rate" (common in
# Pakistani English for @) must be replaced before the bare " at ".
_SPOKEN_EMAIL_SUBS = [
    (" at the rate ", "@"),
    (" at ", "@"),
    (" dot ", "."),
    (" underscore ", "_"),
    (" dash ", "-"),
    (" hyphen ", "-"),
    (" zed ", " z "),
]


def normalize_spoken_email(raw: str | None) -> str | None:
    """Best-effort conversion of a transcribed/spelled email into a real address.

    The extraction model is asked to return a clean address, but transcripts have
    landed in the DB as literal spoken words before (observed live:
    "m a l a i k a dot r i zed v i at ilsainteractive dot com") — this is the
    server-side guard. Returns a lowercase, space-free address only if the result
    validates as a real email; None means "don't store it" (a missing email is
    fine, a wrong one is not).
    """
    if not raw:
        return None
    s = f" {raw.strip().lower()} "
    already_has_at = "@" in s
    for old, new in _SPOKEN_EMAIL_SUBS:
        if old == " at " and already_has_at:
            continue  # "@" already present: a bare spoken "at" is part of a name/word
        s = s.replace(old, new)
    s = re.sub(r"\s+", "", s)
    if not EMAIL_RE.match(s):
        return None
    local, _, domain = s.rpartition("@")
    # Gmail locals can only contain letters/digits/dots — underscores etc. get
    # rejected by Gmail, so an address that "looks fine" silently bounces. Strip
    # anything else out to recover the real address.
    if domain in ("gmail.com", "googlemail.com"):
        local = re.sub(r"[^a-z0-9.]", "", local)
        s = f"{local}@{domain}"
        if not EMAIL_RE.match(s):
            return None
    return s
