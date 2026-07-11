"""OpenAI Responses API integration."""

from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)

from app.config import Settings
from app.prompts.summarizer_prompt import build_summary_input, build_summary_instructions
from app.utils.exceptions import SummarizationError
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def summarize(text: str, settings: Settings) -> str:
    """Generate a summary with the OpenAI Responses API without blocking the event loop."""

    if settings.openai_api_key is None:
        raise SummarizationError("OpenAI is not configured. Please contact the administrator.", 503)
    client = AsyncOpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        timeout=settings.openai_timeout_seconds,
        max_retries=settings.openai_max_retries,
    )
    try:
        response = await client.responses.create(
            model=settings.openai_model,
            instructions=build_summary_instructions(settings.summary_word_target),
            input=build_summary_input(text[:settings.max_summary_input_characters]),
            temperature=0.2,
        )
    except AuthenticationError as exc:
        logger.error("openai_authentication_failed")
        raise SummarizationError("The summarization service is not configured correctly.", 503, "error") from exc
    except RateLimitError as exc:
        logger.warning("openai_rate_limit")
        raise SummarizationError("The summarization service is busy. Please try again shortly.", 429) from exc
    except APITimeoutError as exc:
        raise SummarizationError("The summarization request timed out. Please try again.", 504) from exc
    except BadRequestError as exc:
        logger.error("openai_bad_request")
        raise SummarizationError("The document could not be summarized. Please try a different PDF.", 422) from exc
    except (APIConnectionError, APIError) as exc:
        logger.exception("openai_request_failed")
        raise SummarizationError("Unable to generate a summary right now. Please try again.", 503, "error") from exc
    finally:
        await client.close()
    summary = (response.output_text or "").strip()
    if not summary:
        raise SummarizationError("The summarization service returned an empty response. Please try again.", 502, "error")
    logger.info("openai_summary_generated input_characters=%s output_words=%s", len(text), len(summary.split()))
    return summary
