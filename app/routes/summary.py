"""PDF summarization endpoint."""

from time import perf_counter
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.config import Settings
from app.routes.dependencies import get_app_settings, verify_api_key
from app.schemas.summary import SummaryResponse
from app.services.pdf_service import extract_text_async, read_and_validate_pdf
from app.services.summarizer import summarize
from app.utils.logger import get_logger

router = APIRouter(prefix="/api", tags=["summaries"], dependencies=[Depends(verify_api_key)])
logger = get_logger(__name__)


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_pdf(
    file: Annotated[UploadFile, File(description="A text-based PDF no larger than 20 MB")],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> SummaryResponse:
    """Extract PDF text and return a concise AI-generated summary."""

    started_at = perf_counter()
    try:
        filename, pdf_content = await read_and_validate_pdf(file, settings)
        text = await extract_text_async(pdf_content, settings, filename)
        summary = await summarize(text, settings)
    finally:
        await file.close()
    duration = round(perf_counter() - started_at, 2)
    logger.info("summary_completed filename=%s duration_seconds=%.2f", filename, duration)
    return SummaryResponse(summary=summary, word_count=len(summary.split()), processing_time_seconds=duration)
