# AI Outreach Platform (Telegram User Accounts)

MVP-платформа для поиска релевантных запросов в Telegram-чатах, AI-оценки лидов, подготовки персонального ответа и ведения воронки по проектам.

Важно:
- Используются пользовательские аккаунты Telegram (не Telegram Bot API), потому что боты не всегда могут инициировать диалог первыми.
- Проект ориентирован на соблюдение лимитов, прозрачность коммуникации и контроль оператором.
- Не включает обход банов, взлом ограничений, маскировку под другого человека или иные нарушения правил платформ.

## Что уже есть в репозитории

- Документация по требованиям и архитектуре.
- Каркас backend (FastAPI + SQLite + SQLAlchemy).
- Примитивный web-интерфейс для работы с проектом и лидами.
- Заготовки сервисов для ingest/pipeline (Telegram -> AI scoring -> outreach queue).

## Структура

docs/
- 01_requirements_ru.md
- 02_architecture_ru.md

src/
- app.py
- config.py
- database.py
- models.py
- schemas.py
- services/
  - lead_scoring.py
  - limiter.py
  - outreach_engine.py
  - telegram_ingest.py

web/
- templates/
  - index.html
  - project.html

## Быстрый старт

1. Создай виртуальное окружение и установи зависимости:

	pip install -r requirements.txt

2. Заполни переменные в `.env.repo` (репозиторный вариант) или в `.env`.

3. Запусти сервер:

	uvicorn src.app:app --reload --host 0.0.0.0 --port 8080

4. Открой:

	http://localhost:8080

5. Расширяй словарь фильтрации в файле:

  config/keyword_pack_youtube_ru.json

## Worker Queue

- `Approve/Send` переводит лид в `ready_to_send`.
- Фоновый worker обрабатывает очередь `ready_to_send` и ставит финальный статус `sent:<account_alias>`.
- Лимиты аккаунта применяются в worker перед каждой отправкой.

## Docker запуск

1. Заполни `.env.repo`.
2. Запусти сервисы:

	docker compose up --build

3. API доступен на `http://localhost:8080`, worker запущен отдельным контейнером.

## Следующий шаг для боевого контура

1. Подключить Telegram client sessions (Telethon) и слушать целевые чаты.
2. Подключить LLM-провайдер для scoring и генерации оффера.
3. Включить human-in-the-loop перед первой отправкой в личку.
4. Настроить лимиты на аккаунт/час/день и ротацию по очереди.
5. Добавить статусную аналитику: contacted, replied, booked call, won.