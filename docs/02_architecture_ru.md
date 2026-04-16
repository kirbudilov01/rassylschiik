# 02. Архитектура MVP (RU)

## Поток данных
1. Telegram Ingest Service читает новые сообщения в целевых чатах.
2. Keyword Gate выделяет кандидатов по ключевым словам/фразам и stop-list.
3. AI Lead Scoring Service получает полный payload отправителя (чат, user, текст, keyword matches) и оценивает релевантность (score + rationale).
4. Outreach Engine создает задачу на контакт, если score >= threshold.
5. Limiter проверяет квоты аккаунта (час/день/интервал).
6. Human Review (UI) подтверждает или отклоняет отправку.
7. Sender Service отправляет сообщение от user account и пишет лог.

## Компоненты
- API + UI: FastAPI.
- DB: SQLite (MVP), дальше PostgreSQL.
- Worker: периодический процесс для pipeline.
- Telegram client: Telethon (следующий этап интеграции).
- AI provider abstraction: локальный интерфейс, чтобы менять провайдера.

## Основные сущности
- Project
- Account
- LeadCandidate
- OutreachTask
- MessageLog

## Политики безопасности
- Ограничение скорости на уровне аккаунта.
- Ручное подтверждение первого касания.
- Запрет на отправку по stop-list.
- Аудит-лог каждой отправки/изменения статуса.

## Этапы развития
1. MVP (текущий): API + UI + mock scoring + manual queue.
2. Integration: Telethon ingest/send + real LLM scoring.
3. Scale: multi-account scheduler + Postgres + background jobs.
4. Ops: алерты, dashboards, retry policy.
