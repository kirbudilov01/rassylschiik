def build_system_prompt() -> str:
    return (
        "Ты — AI-ассистент по квалификации лидов из Telegram-чатов на тему YouTube. "
        "Твоя задача: определить релевантность запроса и, если он подходит, подготовить короткую рекомендацию специалиста @kirbudilov. "
        "Если запрос нерелевантный, вернуть решение skip. "
        "Стиль ответа: нейтрально-дружелюбный, без агрессии, без спама, без ложных обещаний."
    )


def build_user_prompt(
    source_chat: str,
    source_user: str,
    source_message: str,
    matched_keywords: list[str],
    matched_phrases: list[str],
) -> str:
    return (
        "Оцени релевантность лида и верни JSON: "
        "{decision: send|skip, confidence: float, reason: string, message: string}. "
        f"Chat: {source_chat}. "
        f"User: {source_user}. "
        f"Message: {source_message}. "
        f"Keyword hits: {matched_keywords}. "
        f"Phrase hits: {matched_phrases}."
    )
