from smtplib import SMTP_PORT
from pydantic_settings import BaseSettings,  SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):

    UPLOAD_SERVICE_URL: str

    # Database
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: int
    POSTGRES_URL: str

    ACCESS_TOKEN_EXPIRE_MINUTE: int
    JWT_ALGORITHM: str
    JWT_SECRETE: str

    REDIRECT_URL: str

    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTE: int

    SMTP_HOST: str
    SMTP_PORT: int
    EMAIL_FROM: str
    EMAIL_PASSWORD: str

    model_config = SettingsConfigDict(

        env_file=Path(__file__).resolve().parents[0]/".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
