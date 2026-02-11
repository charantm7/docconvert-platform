from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    SUPABASE_CONNECTION_URL: str
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_BUCKET: str

    RABBITMQ_URL: str

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[0]/".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
