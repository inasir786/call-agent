import re
from difflib import SequenceMatcher


def _normalize(text: str) -> str:
    text = text.lower().strip()
    return re.sub(r"[^\w\s]", " ", text)


def _fuzzy_present(value: str, transcript: str, threshold: float) -> bool:
    if value in transcript:
        return True
    window_size = max(len(value), 1)
    step = max(window_size // 4, 1)
    best = 0.0
    for start in range(0, max(len(transcript) - window_size, 0) + 1, step):
        window = transcript[start:start + window_size]
        ratio = SequenceMatcher(None, value, window).ratio()
        if ratio > best:
            best = ratio
    return best >= threshold


def _email_grounded(value: str, transcript: str) -> bool:
    local_part, _, domain = value.partition("@")
    if not domain:
        return _fuzzy_present(value, transcript, 0.72)
    tokens = re.split(r"[.\-_]", local_part) + re.split(r"\.", domain)
    return all(token and token in transcript for token in tokens)


def _program_grounded(value: str, transcript: str, threshold: float) -> bool:
    value_words = set(_normalize(value).split())
    transcript_words = set(_normalize(transcript).split())
    if not value_words:
        return False
    overlap = len(value_words & transcript_words) / len(value_words)
    if overlap >= threshold:
        return True
    return _fuzzy_present(_normalize(value), _normalize(transcript), threshold)


def is_grounded(value: str, transcript: str, field: str = "", threshold: float = 0.72) -> bool:
    if not value or not transcript:
        return False
    normalized_value = _normalize(value)
    normalized_transcript = _normalize(transcript)

    if field == "email":
        return _email_grounded(value.strip().lower(), transcript.lower())
    if field == "program_of_interest":
        return _program_grounded(value, transcript, threshold)
    return _fuzzy_present(normalized_value, normalized_transcript, threshold)
