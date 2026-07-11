"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the application."""

    app_name: str = "AI Document Summarizer"
    app_env: str = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4.1-mini"
    summary_word_target: int = Field(default=150, ge=80, le=300)
    max_pdf_size_bytes: int = Field(default=20 * 1024 * 1024, ge=1)
    max_pdf_pages: int = Field(default=200, ge=1, le=1_000)
    max_summary_input_characters: int = Field(default=100_000, ge=1_000)
    openai_timeout_seconds: float = Field(default=60.0, gt=0, le=300)
    openai_max_retries: int = Field(default=2, ge=0, le=5)
    api_access_key: SecretStr | None = None
    cors_origins: list[str] = Field(default_factory=list)
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        enable_decoding=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str] | None) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL must be a standard logging level.")
        return normalized

    @field_validator("openai_api_key", "api_access_key", mode="before")
    @classmethod
    def blank_secrets_are_unset(cls, value: str | SecretStr | None) -> str | SecretStr | None:
        """Compose supplies blank values for optional secrets; treat them as absent."""

        return None if isinstance(value, str) and not value.strip() else value


@lru_cache
def get_settings() -> Settings:
    """Return a cached application settings instance."""

    return Settings()
