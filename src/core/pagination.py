"""Pagination and scroll loop logic module for MTGA Registrar.

This module manages UI pagination state, page advancement, scrolling loops,
and detection of end-of-collection during card collection export.
"""

import logging
from typing import Callable, Optional

from src.core.exceptions import StateError

logger = logging.getLogger("mtga_registrar.core.pagination")


class PaginationManager:
    """Manages collection pagination, page advancement, and end-of-collection detection."""

    def __init__(
        self,
        max_pages: int = 500,
        consecutive_empty_limit: int = 2,
    ) -> None:
        """Initialize pagination manager.

        Args:
            max_pages: Maximum allowable page turns to prevent infinite loops.
            consecutive_empty_limit: Number of consecutive pages with
                no new cards before terminating.
        """
        self.max_pages = max_pages
        self.consecutive_empty_limit = consecutive_empty_limit
        self.current_page = 0
        self.consecutive_empty_count = 0
        logger.debug(
            "Initialized PaginationManager (max_pages=%d, empty_limit=%d)",
            max_pages,
            consecutive_empty_limit,
        )

    def advance_page(
        self,
        navigate_func: Optional[Callable[[], bool]] = None,
    ) -> bool:
        """Advance to the next page of the collection.

        Args:
            navigate_func: Optional callable that performs the UI action
                (e.g. clicking right arrow). If None, defaults to
                incrementing page counter.

        Returns:
            True if advancement succeeded, False otherwise.

        Raises:
            StateError: If max_pages limit is reached.
        """
        if self.current_page >= self.max_pages:
            raise StateError(f"Reached maximum page limit of {self.max_pages}")

        try:
            success = True
            if navigate_func is not None:
                success = navigate_func()

            if success:
                self.current_page += 1
                logger.debug("Advanced to page %d", self.current_page)
            else:
                logger.warning("Navigation function reported failure")

            return success
        except Exception as e:
            logger.error("Failed to advance page: %s", e, exc_info=True)
            raise StateError(
                f"Pagination advancement failed: {e}", details=str(e)
            ) from e

    def check_end_of_collection(
        self,
        new_cards_found_count: int,
        button_detected: bool = True,
    ) -> bool:
        """Determine if the end of the collection has been reached.

        Args:
            new_cards_found_count: Number of new/unseen cards discovered
                on the current page/scroll.
            button_detected: Whether the right navigation button was
                successfully detected/clickable.

        Returns:
            True if end of collection is reached, False otherwise.
        """
        if not button_detected:
            logger.info("End of collection: Navigation button unavailable")
            return True

        if new_cards_found_count == 0:
            self.consecutive_empty_count += 1
            logger.debug(
                "No new cards found (consecutive empty count: %d/%d)",
                self.consecutive_empty_count,
                self.consecutive_empty_limit,
            )
            if self.consecutive_empty_count >= self.consecutive_empty_limit:
                logger.info("End of collection: Reached consecutive empty limit")
                return True
        else:
            self.consecutive_empty_count = 0

        if self.current_page >= self.max_pages:
            logger.info("End of collection: Reached maximum page limit")
            return True

        return False

    def reset(self) -> None:
        """Reset pagination state."""
        self.current_page = 0
        self.consecutive_empty_count = 0
        logger.debug("Reset PaginationManager state")
