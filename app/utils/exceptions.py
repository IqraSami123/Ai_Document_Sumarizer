"""Application exceptions that are safe to present to API clients."""

from dataclasses import dataclass
from http import HTTPStatus


@dataclass(slots=True)
class AppError(Exception):
    """A known application error with a safe public message."""

    message: str
    status_code: int = HTTPStatus.BAD_REQUEST
    log_level: str = "warning"


class PDFProcessingError(AppError):
    """Raised when a PDF cannot be accepted or parsed."""


class SummarizationError(AppError):
    """Raised when the summarization provider cannot serve a request."""
