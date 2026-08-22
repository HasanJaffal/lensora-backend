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
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list, alias="CORS_ORIGINS")
    secret_key: str | None = Field(default=None, alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expires_minutes: int = Field(default=60 * 24, alias="ACCESS_TOKEN_EXPIRES_MINUTES")
    platform_admin_email: str | None = Field(default=None, alias="PLATFORM_ADMIN_EMAIL")
    platform_admin_password: str | None = Field(default=None, alias="PLATFORM_ADMIN_PASSWORD")
    platform_admin_display_name_en: str = Field(
        default="Platform Admin", alias="PLATFORM_ADMIN_DISPLAY_NAME_EN"
    )
    platform_admin_display_name_ar: str = Field(
        default="مسؤول المنصة", alias="PLATFORM_ADMIN_DISPLAY_NAME_AR"
    )
    supabase_url: str | None = Field(default=None, alias="SUPABASE_URL")
    supabase_service_role_key: str | None = Field(default=None, alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_storage_bucket: str = Field(default="attachments", alias="SUPABASE_STORAGE_BUCKET")
    attachment_signed_url_expires_seconds: int = Field(
        default=3600, alias="ATTACHMENT_SIGNED_URL_EXPIRES_SECONDS"
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
