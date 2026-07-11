"""Response models for document summarization."""

from pydantic import BaseModel, ConfigDict, Field


class SummaryResponse(BaseModel):
    """Summary generated from an uploaded PDF."""

    model_config = ConfigDict(str_strip_whitespace=True)

    summary: str = Field(..., min_length=1, max_length=20_000)
    word_count: int = Field(..., ge=1)
    processing_time_seconds: float = Field(..., ge=0)
