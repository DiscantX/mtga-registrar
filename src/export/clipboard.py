"""System clipboard interaction utilities for MTGA Registrar.

This module provides robust system clipboard reading, writing, clearing, and
waiting utilities using pyperclip, with comprehensive error handling and logging.
"""

import logging
import time
from typing import Optional

import pyperclip

from src.core.exceptions import ExportError

logger = logging.getLogger("mtga_registrar.export.clipboard")


class ClipboardUtility:
    """Utility class for robust system clipboard operations."""

    @staticmethod
    def copy(text: str) -> bool:
        """Copy text to the system clipboard.

        Args:
            text: String text to copy to the clipboard.

        Returns:
            True if successfully copied.

        Raises:
            ExportError: If clipboard copy fails or input is invalid.
        """
        if not isinstance(text, str):
            raise ExportError("Clipboard copy input must be a string string.")
        try:
            pyperclip.copy(text)
            logger.debug(
                "Successfully copied %d characters to system clipboard.", len(text)
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to copy text to system clipboard: %s", e, exc_info=True
            )
            raise ExportError(
                "System clipboard copy operation failed", details=str(e)
            ) from e

    @staticmethod
    def paste() -> Optional[str]:
        """Retrieve text from the system clipboard.

        Returns:
            The clipboard string contents, or None if empty.

        Raises:
            ExportError: If clipboard paste operation fails.
        """
        try:
            content = pyperclip.paste()
            if not content:
                logger.debug("System clipboard is currently empty.")
                return None
            logger.debug(
                "Successfully retrieved %d characters from system clipboard.",
                len(content),
            )
            return str(content)
        except Exception as e:
            logger.error(
                "Failed to read from system clipboard: %s", e, exc_info=True
            )
            raise ExportError(
                "System clipboard paste operation failed", details=str(e)
            ) from e

    @staticmethod
    def clear() -> bool:
        """Clear the contents of the system clipboard.

        Returns:
            True if successfully cleared.

        Raises:
            ExportError: If clearing the clipboard fails.
        """
        try:
            pyperclip.copy("")
            logger.debug("Successfully cleared system clipboard.")
            return True
        except Exception as e:
            logger.error("Failed to clear system clipboard: %s", e, exc_info=True)
            raise ExportError(
                "System clipboard clear operation failed", details=str(e)
            ) from e

    @staticmethod
    def wait_for_clipboard(
        timeout: float = 5.0,
        poll_interval: float = 0.2,
        initial_content: Optional[str] = None,
    ) -> Optional[str]:
        """Wait for clipboard content to change or become non-empty.

        Useful when waiting for MTGA client to populate export data to clipboard.

        Args:
            timeout: Maximum seconds to wait.
            poll_interval: Seconds between clipboard checks.
            initial_content: Optional baseline content to detect changes against.

        Returns:
            New clipboard text content, or None if timeout reached.

        Raises:
            ExportError: If clipboard polling fails.
        """
        start_time = time.time()
        logger.debug("Waiting for clipboard content (timeout=%.1fs)...", timeout)

        while time.time() - start_time < timeout:
            try:
                current = pyperclip.paste()
                if current and current != initial_content:
                    logger.debug(
                        "Detected new clipboard content (%d chars).", len(current)
                    )
                    return str(current)
            except Exception as e:
                logger.warning("Error while polling clipboard: %s", e)
            time.sleep(poll_interval)

        logger.warning(
            "Timeout (%.1fs) reached waiting for clipboard content.", timeout
        )
        return None
