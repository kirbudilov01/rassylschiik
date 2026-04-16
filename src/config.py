from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", ".env.repo"), env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="AI Outreach Platform", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8080, alias="APP_PORT")

    database_url: str = Field(default="sqlite:///./data/app.db", alias="DATABASE_URL")

    tg_account_aliases: str = Field(default="sales_ru_1", alias="TG_ACCOUNT_ALIASES")

    ai_provider: str = Field(default="openai", alias="AI_PROVIDER")
    ai_model: str = Field(default="gpt-4o-mini", alias="AI_MODEL")
    ai_api_key: str = Field(default="", alias="AI_API_KEY")

    outreach_human_review_required: bool = Field(default=True, alias="OUTREACH_HUMAN_REVIEW_REQUIRED")
    max_outreach_per_account_per_hour: int = Field(default=3, alias="MAX_OUTREACH_PER_ACCOUNT_PER_HOUR")
    max_outreach_per_account_per_day: int = Field(default=5, alias="MAX_OUTREACH_PER_ACCOUNT_PER_DAY")
    max_new_dialogs_per_account_per_day: int = Field(default=20, alias="MAX_NEW_DIALOGS_PER_ACCOUNT_PER_DAY")

    min_lead_score: float = Field(default=0.65, alias="MIN_LEAD_SCORE")

    target_keywords: str = Field(
        default="youtube,ютуб,продюсер,продюсирование,монтаж,продвижение,удержание,shorts,reels,контент",
        alias="TARGET_KEYWORDS",
    )
    target_phrases: str = Field(
        default="ищу продюсера,нужен продюсер,нужен специалист по youtube,помогите с youtube,как продвигать youtube",
        alias="TARGET_PHRASES",
    )
    stop_phrases: str = Field(
        default="ищу работу,вакансия,куплю аккаунт,арбитраж,крипта",
        alias="STOP_PHRASES",
    )
    keyword_pack_file: str = Field(default="config/keyword_pack_youtube_ru.json", alias="KEYWORD_PACK_FILE")

    worker_poll_seconds: int = Field(default=8, alias="WORKER_POLL_SECONDS")
    worker_batch_size: int = Field(default=20, alias="WORKER_BATCH_SIZE")

    daily_send_min_target: int = Field(default=3, alias="DAILY_SEND_MIN_TARGET")
    daily_send_max_target: int = Field(default=5, alias="DAILY_SEND_MAX_TARGET")


settings = Settings()
