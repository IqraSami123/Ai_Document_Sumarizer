"""Reusable FastAPI dependencies."""

from hmac import compare_digest
from typing import Annotated

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import Settings, get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_app_settings() -> Settings:
    return get_settings()


async def verify_api_key(
    supplied_key: Annotated[str | None, Security(api_key_header)],
    settings: Annotated[Settings, Security(get_app_settings)],
) -> None:
    """Require X-API-Key when API_ACCESS_KEY is configured."""

    if settings.api_access_key is None:
        return
    if not supplied_key or not compare_digest(supplied_key, settings.api_access_key.get_secret_value()):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "A valid API key is required.")
