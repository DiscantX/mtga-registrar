"""Custom domain exceptions for MTGA Registrar.

This module defines the exception hierarchy used across core, vision,
automation, state management, and export modules.
"""

from typing import Optional


class MTGARegistrarError(Exception):
    """Base exception for all MTGA Registrar domain errors."""

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class VisionError(MTGARegistrarError):
    """Raised when screen capture, template matching, or UI perception fails."""

    pass


class AutomationError(MTGARegistrarError):
    """Raised when mouse movement, keyboard input, or timing automation fails."""

    pass


class StateError(MTGARegistrarError):
    """Raised when state tracking, pagination, or batching encounters an invalid state."""

    pass


class ExportError(MTGARegistrarError):
    """Raised when clipboard handling or decklist parsing fails."""

    pass
