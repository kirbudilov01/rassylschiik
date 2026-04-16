from dataclasses import dataclass

from src.services.keyword_filter import analyze_message


@dataclass
class SelectionResult:
    is_selected: bool
    score: float
    reason: str
    matched_keywords: list[str]
    matched_phrases: list[str]
    matched_stop_phrases: list[str]


def evaluate_candidate(
    source_message: str,
    target_keywords: str | list[str],
    target_phrases: str | list[str],
    stop_phrases: str | list[str],
    min_score: float,
) -> SelectionResult:
    match = analyze_message(
        message=source_message,
        keywords_csv=target_keywords,
        phrases_csv=target_phrases,
        stop_phrases_csv=stop_phrases,
    )

    has_domain_signal = len(match.matched_keywords) > 0
    has_intent_signal = len(match.matched_phrases) > 0

    weighted_score = min(
        1.0,
        (0.45 if has_intent_signal else 0.0)
        + min(0.35, len(match.matched_keywords) * 0.05)
        + (0.20 if ("ищу" in source_message.lower() or "нужен" in source_message.lower()) else 0.0),
    )
    final_score = max(match.score, weighted_score)

    if len(match.matched_stop_phrases) > 0:
        return SelectionResult(
            is_selected=False,
            score=0.0,
            reason=f"Stop-list match: {match.matched_stop_phrases}",
            matched_keywords=match.matched_keywords,
            matched_phrases=match.matched_phrases,
            matched_stop_phrases=match.matched_stop_phrases,
        )

    is_selected = has_domain_signal and final_score >= min_score
    reason = (
        "Selected: domain and intent signals are sufficient"
        if is_selected
        else "Rejected: weak domain/intent signals"
    )

    return SelectionResult(
        is_selected=is_selected,
        score=final_score,
        reason=reason,
        matched_keywords=match.matched_keywords,
        matched_phrases=match.matched_phrases,
        matched_stop_phrases=match.matched_stop_phrases,
    )
