from decimal import Decimal
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=list, alias="CORS_ORIGINS"
    )
    secret_key: str | None = Field(default=None, alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expires_minutes: int = Field(
        default=60 * 24, alias="ACCESS_TOKEN_EXPIRES_MINUTES"
    )
    ai_provider: str = Field(default="anthropic", alias="AI_PROVIDER")
    ai_api_key: str | None = Field(default=None, alias="AI_API_KEY")
    ai_model: str = Field(default="claude-sonnet-5", alias="AI_MODEL")

    deposit_percent: Decimal = Field(default=Decimal("0.40"), alias="DEPOSIT_PERCENT")

    seed_doctor_email: str | None = Field(default=None, alias="SEED_DOCTOR_EMAIL")
    seed_doctor_password: str | None = Field(default=None, alias="SEED_DOCTOR_PASSWORD")
    seed_doctor_display_name_en: str | None = Field(
        default=None, alias="SEED_DOCTOR_DISPLAY_NAME_EN"
    )
    seed_doctor_display_name_ar: str | None = Field(
        default=None, alias="SEED_DOCTOR_DISPLAY_NAME_AR"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
