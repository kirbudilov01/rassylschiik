# 04. Что сделать до получения Telegram API (RU)

Пока нет Telegram API, можно полностью подготовить проект:

1. Настроить переменные в [.env.repo](.env.repo):
- TG_ACCOUNT_ALIASES
- AI_API_KEY
- MIN_LEAD_SCORE
- KEYWORD_PACK_FILE

2. Доработать словари в [config/keyword_pack_youtube_ru.json](config/keyword_pack_youtube_ru.json):
- target_keywords
- target_phrases
- stop_phrases

3. Протестировать отбор через UI:
- открыть проект
- заполнить блок "Тест фразы по словарю"
- убедиться, что релевантные фразы дают is_candidate=true

4. Прогнать ручной ingest:
- добавить тестовые сообщения через форму "Ingest кандидата"
- проверить таблицы "Выбранные сообщения" и "Отправленные сообщения"

5. Выгрузить CSV:
- CSV: выбранные
- CSV: отправленные

6. Целевые метрики на старте:
- selected в день
- sent в день
- conversion selected -> sent

После получения TG_API_ID/TG_API_HASH сразу подключаем Telethon listener + sender.
