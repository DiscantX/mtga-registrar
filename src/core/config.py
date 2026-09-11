"""Configuration and logging infrastructure for MTGA Registrar.

This module provides application settings loaded from environment variables
and structured logging configuration.
"""

import logging
import sys
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings and configuration parameters.

    Attributes:
        log_level: Logging level (e.g., DEBUG, INFO, WARNING, ERROR).
        max_batch_size: Maximum number of cards per exported deck batch.
        confidence_threshold: Minimum confidence score for computer vision detection.
        screenshot_delay: Delay in seconds before capturing screenshots.
    """

    log_level: str = "INFO"
    max_batch_size: int = 250
    confidence_threshold: float = 0.8
    screenshot_delay: float = 0.5

    model_config = SettingsConfigDict(
        env_prefix="MTGA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Global settings instance
settings = Settings()


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """Configure structured logging for the application.

    Args:
        log_level: Optional override for the logging level.

    Returns:
        Configured logger instance for the application.
    """
    level_str = log_level or settings.log_level
    numeric_level = getattr(logging, level_str.upper(), logging.INFO)

    logger = logging.getLogger("mtga_registrar")
    logger.setLevel(numeric_level)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(numeric_level)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
