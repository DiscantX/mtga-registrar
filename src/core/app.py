"""Main application controller module for MTGA Registrar.

This module ties together vision detection, input automation, state management,
pagination, batching, and export transfer handlers into a cohesive collection
export workflow.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from src.core.batching import BatchController
from src.core.config import Settings, settings, setup_logging
from src.core.exceptions import MTGARegistrarError
from src.core.pagination import PaginationManager
from src.core.state import CardEntry, CollectionState
from src.export.base import ClipboardTransferProvider, ExportTransferProvider
from src.export.parser import DeckParser

logger = logging.getLogger("mtga_registrar.core.app")


class ApplicationController:
    """Orchestrates the end-to-end MTGA collection export workflow."""

    def __init__(
        self,
        config: Optional[Settings] = None,
        transfer_provider: Optional[ExportTransferProvider] = None,
    ) -> None:
        """Initialize the application controller.

        Args:
            config: Optional application settings (defaults to global settings).
            transfer_provider: Optional export transfer provider
                (defaults to ClipboardTransferProvider).
        """
        self.settings = config or settings
        setup_logging(self.settings.log_level)
        self.state = CollectionState()
        self.pagination = PaginationManager()
        self.batch_controller = BatchController(
            max_batch_size=self.settings.max_batch_size
        )
        self.transfer_provider = transfer_provider or ClipboardTransferProvider()
        self.parser = DeckParser()
        logger.info("Initialized ApplicationController")

    def initialize(self) -> None:
        """Initialize system components, transfer provider, and logging."""
        logger.info("Initializing application controller components...")
        self.transfer_provider.start()
        logger.info("Application controller initialized successfully.")

    def create_deck(
        self,
        nav_callback: Optional[Callable[[], bool]] = None,
    ) -> bool:
        """Simulate or execute deck creation in the 'Timeless' format.

        Args:
            nav_callback: Optional custom callback for UI navigation.

        Returns:
            True if deck creation succeeded, False otherwise.

        Raises:
            MTGARegistrarError: If deck creation fails.
        """
        logger.info("Creating new deck in 'Timeless' format...")
        try:
            if nav_callback is not None:
                success = nav_callback()
                if not success:
                    raise MTGARegistrarError(
                        "Deck creation navigation callback failed."
                    )
            logger.info("Successfully created deck in 'Timeless' format.")
            return True
        except Exception as e:
            if isinstance(e, MTGARegistrarError):
                raise
            logger.error(f"Deck creation failed: {e}", exc_info=True)
            raise MTGARegistrarError(
                f"Deck creation failed: {e}", details=str(e)
            ) from e

    def scan_page(
        self,
        page_scanner: Optional[Callable[[int], List[CardEntry]]] = None,
    ) -> List[CardEntry]:
        """Scan the current collection page for owned cards.

        Args:
            page_scanner: Optional callable taking current page number
                and returning discovered cards. If None, uses a default
                simulation or stub.

        Returns:
            List of discovered CardEntry objects on the current page.
        """
        current_page = self.pagination.current_page
        logger.info(f"Scanning collection page {current_page}...")

        discovered: List[CardEntry] = []
        if page_scanner is not None:
            discovered = page_scanner(current_page)
        else:
            pass

        added_count = 0
        for card in discovered:
            self.state.add_card(
                name=card.name,
                quantity=card.quantity,
                set_code=card.set_code,
                collector_number=card.collector_number,
                unique_id=card.unique_id,
            )
            added_count += 1

        logger.info(
            "Page %d scan complete: found %d cards (%d processed).",
            current_page,
            len(discovered),
            added_count,
        )
        return discovered

    def export_collection(
        self,
        dry_run: bool = False,
        page_scanner: Optional[Callable[[int], List[CardEntry]]] = None,
        max_pages: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Execute the full collection scanning, pagination, batching, and export workflow.

        Args:
            dry_run: If True, simulate actions without executing physical
                mouse/keyboard commands.
            page_scanner: Optional callable to scan cards per page.
            max_pages: Optional override for maximum pagination limit.

        Returns:
            List of exported batch dictionaries.

        Raises:
            MTGARegistrarError: If export workflow encounters unrecoverable errors.
        """
        logger.info(f"Starting collection export workflow (dry_run={dry_run})...")
        if max_pages is not None:
            self.pagination.max_pages = max_pages

        try:
            self.initialize()
            self.create_deck()

            end_of_collection = False
            while not end_of_collection:
                cards_on_page = self.scan_page(page_scanner)
                new_cards_count = len(cards_on_page)

                end_of_collection = self.pagination.check_end_of_collection(
                    new_cards_found_count=new_cards_count,
                    button_detected=True,
                )

                if not end_of_collection:
                    self.pagination.advance_page()

            total_cards = self.state.get_total_cards()
            unique_cards = self.state.get_unique_cards_count()
            logger.info(
                "Collection scan completed: %d total cards (%d unique).",
                total_cards,
                unique_cards,
            )

            all_cards = self.state.get_all_cards()
            batches = self.batch_controller.create_batches(all_cards)
            logger.info(
                "Created %d export batches (max size %d).",
                len(batches),
                self.settings.max_batch_size,
            )

            for batch in batches:
                batch_id = batch["batch_id"]
                batch_cards = batch["cards"]

                lines = []
                for card in batch_cards:
                    set_part = f" ({card.set_code})" if card.set_code else ""
                    num_part = (
                        f" {card.collector_number}"
                        if card.collector_number
                        else ""
                    )
                    lines.append(
                        f"{card.quantity} {card.name}{set_part}{num_part}"
                    )
                decklist_str = "\n".join(lines)

                logger.info(
                    "Exporting batch %d/%d (%d cards)...",
                    batch_id,
                    len(batches),
                    len(batch_cards),
                )
                if not dry_run:
                    self.transfer_provider.transfer(decklist_str)
                self.batch_controller.mark_batch_exported(batch_id)
                batch["exported_data"] = decklist_str

            logger.info(
                "All collection export batches successfully processed and exported."
            )
            return batches

        except Exception as e:
            logger.error(f"Collection export workflow failed: {e}", exc_info=True)
            if isinstance(e, MTGARegistrarError):
                raise
            raise MTGARegistrarError(
                f"Export workflow failed: {e}", details=str(e)
            ) from e
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop transfer provider and clean up resources."""
        logger.info("Stopping application controller...")
        try:
            self.transfer_provider.stop()
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
