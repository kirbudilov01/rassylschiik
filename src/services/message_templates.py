from hashlib import md5


OUTREACH_TEMPLATES = [
    "Привет, увидел ваш вопрос по YouTube в чате. Мне рекомендовали по продюсированию @kirbudilov, можете ему написать, думаю, что есть решение под вашу задачу.",
    "Привет! Заметил ваш запрос по YouTube. Если актуально, рекомендую написать @kirbudilov по продюсированию, он как раз решает такие кейсы.",
    "Добрый день. По вашему вопросу в чате по YouTube могу порекомендовать @kirbudilov, у него сильная экспертиза в продюсировании и росте каналов.",
]


def choose_template(source_user: str, source_message: str) -> str:
    key = f"{source_user}:{source_message}".encode("utf-8")
    idx = int(md5(key).hexdigest(), 16) % len(OUTREACH_TEMPLATES)
    return OUTREACH_TEMPLATES[idx]
