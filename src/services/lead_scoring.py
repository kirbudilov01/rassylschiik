from dataclasses import dataclass


@dataclass
class ScoreResult:
    score: float
    reason: str
    draft: str


YOUTUBE_KEYWORDS = [
    "youtube",
    "ютуб",
    "продюсер",
    "монтаж",
    "продвижение",
    "обложка",
    "сценарий",
    "удержание",
    "reels",
    "shorts",
]


def score_message(source_message: str, offer_text: str, destination_link: str) -> ScoreResult:
    text = source_message.lower()
    hits = sum(1 for keyword in YOUTUBE_KEYWORDS if keyword in text)
    score = min(1.0, 0.2 + hits * 0.12)

    if hits == 0:
        reason = "Нет совпадений по ключевым YouTube-фразам"
    else:
        reason = f"Найдено {hits} тематических совпадений"

    draft = (
        "Привет! Увидел ваш запрос по YouTube. "
        f"{offer_text} "
        f"Если удобно, вот ссылка с деталями: {destination_link}"
    )
    return ScoreResult(score=score, reason=reason, draft=draft)
