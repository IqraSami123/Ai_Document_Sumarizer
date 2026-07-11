"""Centralized application logging."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure console and rotating file logs once per process."""

    log_directory = Path(__file__).resolve().parents[2] / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    file_handler = RotatingFileHandler(log_directory / "application.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Return a named application logger."""

    return logging.getLogger(name)
