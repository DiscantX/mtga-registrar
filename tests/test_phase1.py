"""Baseline unit tests for Phase 1 components.

Verifies custom exceptions, configuration settings, and logging infrastructure.
"""

import logging

import pytest

from src.core.config import Settings, setup_logging
from src.core.exceptions import (
    AutomationError,
    ExportError,
    MTGARegistrarError,
    StateError,
    VisionError,
)


def test_exception_hierarchy() -> None:
    """Verify all domain exceptions inherit from MTGARegistrarError and format correctly."""
    base_err = MTGARegistrarError("Base error occurred", "some details")
    assert str(base_err) == "Base error occurred (Details: some details)"

    vision_err = VisionError("Vision failed")
    assert isinstance(vision_err, MTGARegistrarError)
    assert str(vision_err) == "Vision failed"

    with pytest.raises(VisionError):
        raise VisionError("Vision failed")

    auto_err = AutomationError("Automation failed")
    assert isinstance(auto_err, MTGARegistrarError)

    state_err = StateError("State error")
    assert isinstance(state_err, MTGARegistrarError)

    export_err = ExportError("Export error")
    assert isinstance(export_err, MTGARegistrarError)


def test_settings_defaults() -> None:
    """Verify default configuration settings."""
    settings = Settings()
    assert settings.log_level == "INFO"
    assert settings.max_batch_size == 250
    assert settings.confidence_threshold == 0.8
    assert settings.screenshot_delay == 0.5


def test_setup_logging() -> None:
    """Verify logging setup creates a functional logger."""
    logger = setup_logging("DEBUG")
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) > 0
