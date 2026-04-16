from dataclasses import dataclass


@dataclass
class KeywordMatchResult:
    is_candidate: bool
    matched_keywords: list[str]
    matched_phrases: list[str]
    matched_stop_phrases: list[str]
    score: float


def _split_csv(csv_value: str) -> list[str]:
    return [item.strip().lower() for item in csv_value.split(",") if item.strip()]


def _normalize_terms(raw: str | list[str]) -> list[str]:
    if isinstance(raw, str):
        return _split_csv(raw)
    return [item.strip().lower() for item in raw if item and item.strip()]


def analyze_message(
    message: str,
    keywords_csv: str | list[str],
    phrases_csv: str | list[str],
    stop_phrases_csv: str | list[str],
) -> KeywordMatchResult:
    text = message.lower()
    keywords = _normalize_terms(keywords_csv)
    phrases = _normalize_terms(phrases_csv)
    stop_phrases = _normalize_terms(stop_phrases_csv)

    matched_keywords = [kw for kw in keywords if kw in text]
    matched_phrases = [phrase for phrase in phrases if phrase in text]
    matched_stop_phrases = [phrase for phrase in stop_phrases if phrase in text]

    score = min(1.0, len(matched_keywords) * 0.12 + len(matched_phrases) * 0.25 - len(matched_stop_phrases) * 0.5)
    is_candidate = (len(matched_keywords) > 0 or len(matched_phrases) > 0) and len(matched_stop_phrases) == 0

    return KeywordMatchResult(
        is_candidate=is_candidate,
        matched_keywords=matched_keywords,
        matched_phrases=matched_phrases,
        matched_stop_phrases=matched_stop_phrases,
        score=max(0.0, score),
    )
