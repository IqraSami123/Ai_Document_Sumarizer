"""In-memory validation and extraction for PDF uploads."""

import asyncio
from pathlib import PurePath

import fitz
from fastapi import UploadFile, status

from app.config import Settings
from app.utils.exceptions import PDFProcessingError
from app.utils.logger import get_logger

logger = get_logger(__name__)
PDF_SIGNATURE = b"%PDF-"
PDF_MIME_TYPES = frozenset({"application/pdf", "application/x-pdf"})


def safe_filename(filename: str | None) -> str:
    # PurePath strips both POSIX and Windows traversal components.
    return PurePath((filename or "").replace("\\", "/")).name or "upload.pdf"


async def read_and_validate_pdf(upload: UploadFile, settings: Settings) -> tuple[str, bytes]:
    """Validate metadata and read a bounded PDF entirely in memory."""

    filename = safe_filename(upload.filename)
    if not filename.lower().endswith(".pdf"):
        raise PDFProcessingError("Only PDF files are accepted.", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
    content_type = (upload.content_type or "").lower().strip()
    if content_type and content_type not in PDF_MIME_TYPES:
        raise PDFProcessingError("The uploaded file MIME type is not PDF.", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
    if upload.size is not None and upload.size > settings.max_pdf_size_bytes:
        raise PDFProcessingError("PDF files must be 20 MB or smaller.", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    content = bytearray()
    while chunk := await upload.read(1024 * 1024):
        content.extend(chunk)
        if len(content) > settings.max_pdf_size_bytes:
            raise PDFProcessingError("PDF files must be 20 MB or smaller.", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    if not content:
        raise PDFProcessingError("The uploaded PDF is empty.", status.HTTP_422_UNPROCESSABLE_ENTITY)
    if not content.startswith(PDF_SIGNATURE):
        raise PDFProcessingError("The uploaded file is not a valid PDF.", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
    logger.info("accepted_pdf filename=%s size_bytes=%s", filename, len(content))
    return filename, bytes(content)


def extract_text(pdf_content: bytes, settings: Settings, filename: str) -> str:
    """Reject corrupted/encrypted PDFs and safely normalize extracted text."""

    try:
        with fitz.open(stream=pdf_content, filetype="pdf") as document:
            if document.needs_pass:
                raise PDFProcessingError("Encrypted PDFs are not supported.", status.HTTP_422_UNPROCESSABLE_ENTITY)
            if document.page_count == 0:
                raise PDFProcessingError("The PDF contains no pages.", status.HTTP_422_UNPROCESSABLE_ENTITY)
            if document.page_count > settings.max_pdf_pages:
                raise PDFProcessingError("This PDF has too many pages to process.", status.HTTP_422_UNPROCESSABLE_ENTITY)
            text = "\n".join(page.get_text("text") for page in document)
    except PDFProcessingError:
        raise
    except Exception as exc:
        logger.info("unreadable_pdf filename=%s error=%s", filename, type(exc).__name__)
        raise PDFProcessingError("This PDF is corrupted or cannot be read.", status.HTTP_422_UNPROCESSABLE_ENTITY) from exc
    normalized = " ".join(text.split())
    if not normalized:
        raise PDFProcessingError("This PDF does not contain extractable text.", status.HTTP_422_UNPROCESSABLE_ENTITY)
    logger.info("extracted_pdf_text filename=%s characters=%s", filename, len(normalized))
    return normalized


async def extract_text_async(pdf_content: bytes, settings: Settings, filename: str) -> str:
    """Run CPU-bound PDF parsing outside the event loop."""

    return await asyncio.to_thread(extract_text, pdf_content, settings, filename)
