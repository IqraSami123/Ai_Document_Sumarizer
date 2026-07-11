"""Application factory and HTTP configuration."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.exception_handlers import register_exception_handlers
from app.middleware import RequestContextMiddleware
from app.routes import health, summary, web
from app.utils.logger import configure_logging, get_logger

BASE_DIR = Path(__file__).resolve().parent
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)
    app.state.settings = settings
    logger.info("application_started environment=%s", settings.app_env)
    yield
    logger.info("application_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug, version="1.0.0", lifespan=lifespan)
    if settings.cors_origins:
        app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"])
    app.add_middleware(RequestContextMiddleware)
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
    app.include_router(web.router)
    app.include_router(health.router)
    app.include_router(summary.router)
    register_exception_handlers(app)
    return app


app = create_app()
