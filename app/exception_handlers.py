"""Central safe exception handling."""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.utils.exceptions import AppError
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _response(request: Request, status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "request_id": getattr(request.state, "request_id", None)},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        getattr(logger, exc.log_level)("request_id=%s %s", getattr(request.state, "request_id", None), exc.message)
        return _response(request, exc.status_code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, _: RequestValidationError) -> JSONResponse:
        return _response(request, status.HTTP_422_UNPROCESSABLE_ENTITY, "The request data is invalid.")

    @app.exception_handler(HTTPException)
    async def handle_http_error(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "The request could not be completed."
        return _response(request, exc.status_code, detail)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, _: Exception) -> JSONResponse:
        logger.exception("request_id=%s unexpected error", getattr(request.state, "request_id", None))
        return _response(request, status.HTTP_500_INTERNAL_SERVER_ERROR, "An unexpected error occurred. Please try again.")
