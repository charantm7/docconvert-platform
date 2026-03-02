from pydantic_settings import BaseSettings,  SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):


    # Database
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: int
    POSTGRES_URL: str


    model_config = SettingsConfigDict(

        env_file=Path(__file__).resolve().parents[0]/".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
