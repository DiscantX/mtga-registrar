"""Batch chunking controller module for MTGA Registrar.

This module handles splitting collected cards into batches of up to 250 cards per deck
(matching MTGA deck limits), tracking batch export queues and generation status.
"""

import logging
from typing import Any, Dict, List, Optional

from src.core.config import settings
from src.core.exceptions import StateError

logger = logging.getLogger("mtga_registrar.core.batching")


class BatchController:
    """Manages batching of collected cards into deck export chunks."""

    def __init__(self, max_batch_size: Optional[int] = None) -> None:
        """Initialize batch controller.

        Args:
            max_batch_size: Maximum cards per deck batch
                (defaults to settings.max_batch_size, i.e., 250).
        """
        self.max_batch_size = max_batch_size or settings.max_batch_size
        if self.max_batch_size <= 0:
            raise StateError(
                f"Max batch size must be positive, got {self.max_batch_size}"
            )
        self._batches: List[Dict[str, Any]] = []
        logger.debug(
            "Initialized BatchController with max_batch_size=%d",
            self.max_batch_size,
        )

    def chunk_cards(self, cards: List[Any]) -> List[List[Any]]:
        """Split a list of cards into chunks respecting max_batch_size.

        Args:
            cards: List of cards or card entries.

        Returns:
            List of card lists, each containing at most max_batch_size items.

        Raises:
            StateError: If chunking encounters invalid input.
        """
        if not isinstance(cards, list):
            raise StateError("Cards input must be a list")

        try:
            chunks = []
            for i in range(0, len(cards), self.max_batch_size):
                chunk = cards[i : i + self.max_batch_size]
                chunks.append(chunk)
            logger.debug(
                "Chunked %d cards into %d batches of max size %d",
                len(cards),
                len(chunks),
                self.max_batch_size,
            )
            return chunks
        except Exception as e:
            logger.error("Failed to chunk cards: %s", e, exc_info=True)
            raise StateError(
                f"Card chunking failed: {e}", details=str(e)
            ) from e

    def create_batches(self, cards: List[Any]) -> List[Dict[str, Any]]:
        """Create structured batch objects from a list of cards.

        Args:
            cards: List of cards or card entries.

        Returns:
            List of batch dictionaries containing batch ID, cards, status, and size.
        """
        chunks = self.chunk_cards(cards)
        self._batches = []
        for idx, chunk in enumerate(chunks, start=1):
            batch = {
                "batch_id": idx,
                "cards": chunk,
                "size": len(chunk),
                "status": "pending",
            }
            self._batches.append(batch)

        logger.info(
            "Created %d export batches from %d total cards",
            len(self._batches),
            len(cards),
        )
        return self._batches

    def get_batches(self) -> List[Dict[str, Any]]:
        """Retrieve all managed export batches.

        Returns:
            List of batch dictionaries.
        """
        return self._batches

    def get_pending_batches(self) -> List[Dict[str, Any]]:
        """Retrieve batches that have not yet been exported.

        Returns:
            List of pending batch dictionaries.
        """
        return [b for b in self._batches if b["status"] == "pending"]

    def mark_batch_exported(self, batch_id: int) -> None:
        """Mark a specific batch as exported.

        Args:
            batch_id: ID of the batch to mark exported.

        Raises:
            StateError: If batch_id is not found.
        """
        for batch in self._batches:
            if batch["batch_id"] == batch_id:
                batch["status"] = "exported"
                logger.debug("Marked batch %d as exported", batch_id)
                return
        raise StateError(f"Batch ID {batch_id} not found")

    def reset(self) -> None:
        """Reset batch controller state."""
        self._batches.clear()
        logger.debug("Reset BatchController state")
