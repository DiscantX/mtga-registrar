"""Pluggable export transfer interface and default providers.

This module defines the abstract base class `ExportTransferProvider` and concrete
providers such as `ClipboardTransferProvider` for native clipboard interaction.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

import pyperclip

from src.core.exceptions import ExportError

logger = logging.getLogger("mtga_registrar")


class ExportTransferProvider(ABC):
    """Abstract base class for exporting or transferring deck/collection data."""

    @abstractmethod
    def transfer(self, data: str) -> bool:
        """Transfer or export the given deck/collection data string.

        Args:
            data: The string representation of the deck or collection.

        Returns:
            True if transfer/export was successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_data(self) -> Optional[str]:
        """Retrieve any received or stored data.

        Returns:
            The stored data string if available, or None.
        """
        pass

    @abstractmethod
    def start(self) -> None:
        """Start the transfer provider."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop or clean up the transfer provider."""
        pass


class ClipboardTransferProvider(ExportTransferProvider):
    """Native system clipboard export provider using pyperclip."""

    def transfer(self, data: str) -> bool:
        """Copy the given deck data string to the system clipboard.

        Args:
            data: The decklist string to copy.

        Returns:
            True if successful.

        Raises:
            ExportError: If clipboard interaction fails.
        """
        try:
            if not isinstance(data, str):
                raise ExportError("Clipboard transfer data must be a string.")
            pyperclip.copy(data)
            logger.debug("Successfully copied deck data to system clipboard.")
            return True
        except Exception as e:
            logger.error(f"Failed to copy data to clipboard: {e}")
            raise ExportError("System clipboard copy failed", details=str(e)) from e

    def get_data(self) -> Optional[str]:
        """Retrieve the current contents of the system clipboard.

        Returns:
            The clipboard string contents, or None if empty/unavailable.

        Raises:
            ExportError: If reading clipboard fails.
        """
        try:
            content = pyperclip.paste()
            return content if content else None
        except Exception as e:
            logger.error(f"Failed to read from clipboard: {e}")
            raise ExportError("System clipboard paste failed", details=str(e)) from e

    def start(self) -> None:
        """Initialize clipboard provider (no-op)."""
        logger.debug("ClipboardTransferProvider started.")

    def stop(self) -> None:
        """Stop clipboard provider (no-op)."""
        logger.debug("ClipboardTransferProvider stopped.")
