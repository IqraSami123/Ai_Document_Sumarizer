"""Operational health-check routes."""

from fastapi import APIRouter, Response, status

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", status_code=status.HTTP_200_OK)
async def health_check(response: Response) -> dict[str, str]:
    """Return basic process health information."""

    response.headers["Cache-Control"] = "no-store"
    return {"status": "ok"}
