"""Main application controller module for MTGA Registrar.

This module ties together vision detection, input automation, state management,
pagination, batching, and export transfer handlers into a cohesive collection
export workflow.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from src.automation.browser import BrowserController
from src.automation.emergency_stop import EmergencyStop
from src.automation.keyboard import KeyboardController
from src.automation.mouse import MouseController
from src.automation.timing import sleep_random
from src.core.batching import BatchController
from src.core.config import Settings, settings, setup_logging
from src.core.exceptions import MTGARegistrarError
from src.core.pagination import PaginationManager
from src.core.scan_cursor import PartialCard, ScanCursor
from src.core.state import CardEntry, CollectionState
from src.core.ui_locations import get_click_point
from src.export.base import ClipboardTransferProvider, ExportTransferProvider
from src.export.parser import DeckParser
from src.vision.capture import ScreenCapture
from src.vision.detector import TemplateDetector
from src.vision.ui import UIDetector

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
        self.cursor = ScanCursor()
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
            logger.info("[SEQ:create_deck] Clicking '+' Create Deck button, no format selected.")
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

    def scan_and_click_page(
        self,
        remaining_capacity: int,
        page_scanner: Optional[Callable[[int], List[CardEntry]]] = None,
    ) -> tuple[List[CardEntry], bool]:
        """Scan the current collection page and click owned cards into the open deck.

        Resumes from `self.cursor.slot_index`, first finishing any card recorded in
        `self.cursor.partial_card`, then continuing through the rest of the page.
        Stops early (returning `page_fully_scanned=False`) if `remaining_capacity`
        copies are used up mid-page, recording the exact resume point in the cursor.

        Args:
            remaining_capacity: Number of card copies still allowed in the current
                in-game deck before hitting the 250-copy limit.
            page_scanner: Optional test-injection callable returning the full list
                of CardEntry for the current page. When provided, this method
                simulates slot-by-slot processing over that list instead of using
                real screen capture / template detection / mouse clicks.

        Returns:
            Tuple of (cards_added_this_call, page_fully_scanned). If
            page_fully_scanned is False, `self.cursor` has been updated with the
            exact slot/partial-card state needed to resume next time.
        """
        logger.info(
            "[SEQ:scan_page] Calculating grid, counting diamonds/infinity, clicking cards."
        )
        cards_added: List[CardEntry] = []
        capacity_left = remaining_capacity

        if page_scanner is not None:
            all_cards = page_scanner(self.pagination.current_page)
            slot_index = self.cursor.slot_index
            loop_start = slot_index

            if self.cursor.partial_card is not None:
                pc = self.cursor.partial_card
                take = min(pc.remaining_qty, capacity_left)
                if take > 0:
                    self.state.add_card(
                        name=pc.name, quantity=take, set_code=pc.set_code,
                        collector_number=pc.collector_number, unique_id=pc.unique_id,
                    )
                    cards_added.append(CardEntry(
                        name=pc.name, quantity=take, set_code=pc.set_code,
                        collector_number=pc.collector_number, unique_id=pc.unique_id,
                    ))
                    capacity_left -= take
                if take < pc.remaining_qty:
                    pc.remaining_qty -= take
                    return cards_added, False
                self.cursor.partial_card = None
                loop_start = slot_index + 1

            for idx in range(loop_start, len(all_cards)):
                card = all_cards[idx]
                qty = card.quantity
                if qty <= 0:
                    continue

                take = min(qty, capacity_left)
                entry = None
                if take > 0:
                    entry = self.state.add_card(
                        name=card.name, quantity=take, set_code=card.set_code,
                        collector_number=card.collector_number,
                    )
                    cards_added.append(CardEntry(
                        name=card.name, quantity=take, set_code=card.set_code,
                        collector_number=card.collector_number,
                        unique_id=entry.unique_id,
                    ))
                    capacity_left -= take

                if take < qty:
                    fallback_uid = (
                        f"{card.name.strip().lower()}_"
                        f"{(card.set_code or '').strip().lower()}_"
                        f"{(card.collector_number or '').strip().lower()}"
                    )
                    self.cursor.slot_index = idx
                    self.cursor.partial_card = PartialCard(
                        name=card.name, set_code=card.set_code,
                        collector_number=card.collector_number,
                        unique_id=(entry.unique_id if entry is not None else fallback_uid),
                        remaining_qty=qty - take,
                    )
                    return cards_added, False

            self.cursor.slot_index = 0
            return cards_added, True

        # Real vision/mouse path
        image = ScreenCapture.capture_screen()
        grid_boxes = TemplateDetector.calculate_card_grid(image.shape)
        start_slot = self.cursor.slot_index
        loop_start = start_slot

        if self.cursor.partial_card is not None:
            pc = self.cursor.partial_card
            if start_slot < len(grid_boxes):
                bx, by, bw, bh = grid_boxes[start_slot]
                center_x = bx + bw // 2
                center_y = by + bh // 2
                take = min(pc.remaining_qty, capacity_left)
                for _ in range(take):
                    EmergencyStop.check()
                    MouseController.click(center_x, center_y)
                    sleep_random(0.05, 0.01, 0.02, 0.1)
                if take > 0:
                    self.state.add_card(
                        name=pc.name, quantity=take, set_code=pc.set_code,
                        collector_number=pc.collector_number, unique_id=pc.unique_id,
                    )
                    cards_added.append(CardEntry(
                        name=pc.name, quantity=take, set_code=pc.set_code,
                        collector_number=pc.collector_number, unique_id=pc.unique_id,
                    ))
                    capacity_left -= take
                if take < pc.remaining_qty:
                    pc.remaining_qty -= take
                    return cards_added, False
            self.cursor.partial_card = None
            loop_start = start_slot + 1

        for idx in range(loop_start, len(grid_boxes)):
            EmergencyStop.check()
            bx, by, bw, bh = grid_boxes[idx]
            slot_img = image[by:by + bh, bx:bx + bw]
            qty = TemplateDetector.evaluate_card_ownership(slot_img)
            if qty <= 0:
                continue

            center_x = bx + bw // 2
            center_y = by + bh // 2
            take = min(qty, capacity_left)

            for _ in range(take):
                EmergencyStop.check()
                MouseController.click(center_x, center_y)
                sleep_random(0.05, 0.01, 0.02, 0.1)

            card_name = f"Card_{self.pagination.current_page}_{idx}"
            entry = None
            if take > 0:
                entry = self.state.add_card(name=card_name, quantity=take)
                cards_added.append(
                    CardEntry(name=card_name, quantity=take, unique_id=entry.unique_id)
                )
                capacity_left -= take

            if take < qty:
                fallback_uid = f"{card_name.strip().lower()}__"
                self.cursor.slot_index = idx
                self.cursor.partial_card = PartialCard(
                    name=card_name, set_code=None, collector_number=None,
                    unique_id=(entry.unique_id if entry is not None else fallback_uid),
                    remaining_qty=qty - take,
                )
                return cards_added, False

        MouseController.scroll_down(clicks=5)
        sleep_random(0.5, 0.1, 0.2, 0.5)
        self.cursor.slot_index = 0
        return cards_added, True

    def _scroll_to_page(self, target_page: int) -> None:
        """Scroll down to reach a specific collection page after a fresh deck-builder session.

        The collection view always resets to page 1 when a new deck is created, so
        this must be called at the start of every batch cycle after the first
        whenever the cursor is not already on page 0.

        Args:
            target_page: Zero-based page index to scroll to.
        """
        logger.info("Scrolling back to page %d to resume scanning.", target_page)
        for _ in range(target_page):
            EmergencyStop.check()
            MouseController.scroll_down(clicks=5)
            sleep_random(0.5, 0.1, 0.2, 0.5)

    def export_collection(
        self,
        dry_run: bool = False,
        page_scanner: Optional[Callable[[int], List[CardEntry]]] = None,
        max_pages: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Execute the full collection scanning, pagination, batching, and export workflow.

        Repeats a create-deck -> scan/click up to the 250-copy limit -> save ->
        export -> cleanup cycle until the entire collection has been scanned,
        resuming exactly where the previous batch left off (including a partially
        clicked card) since the in-game collection view resets to page 1 every time
        a new deck is created.

        Args:
            dry_run: If True, simulate actions without executing physical
                mouse/keyboard commands or browser/transfer steps.
            page_scanner: Optional callable to scan cards per page (test injection).
            max_pages: Optional override for maximum pagination limit.

        Returns:
            List of exported batch dictionaries.

        Raises:
            MTGARegistrarError: If export workflow encounters unrecoverable errors.
        """
        logger.info(f"Starting collection export workflow (dry_run={dry_run})...")
        if max_pages is not None:
            self.pagination.max_pages = max_pages

        EmergencyStop.reset()
        self.cursor.reset()
        self.pagination.reset()
        max_copies_per_batch = self.settings.max_batch_size

        try:
            self.initialize()
            exported_batches: List[Dict[str, Any]] = []
            batch_num = 0
            first_cycle = True
            collection_exhausted = False

            while not collection_exhausted:
                EmergencyStop.check()
                self.create_deck()

                if self.cursor.page > 0 and page_scanner is None:
                    self._scroll_to_page(self.cursor.page)

                batch_cards: List[CardEntry] = []
                copies_in_batch = 0
                batch_full = False

                while not batch_full:
                    EmergencyStop.check()
                    remaining_capacity = max_copies_per_batch - copies_in_batch
                    added, page_fully_scanned = self.scan_and_click_page(
                        remaining_capacity, page_scanner
                    )
                    batch_cards.extend(added)
                    copies_in_batch += sum(c.quantity for c in added)

                    if not page_fully_scanned:
                        batch_full = True
                        break

                    new_cards_count = len(added)
                    collection_exhausted = self.pagination.check_end_of_collection(
                        new_cards_found_count=new_cards_count,
                        button_detected=True,
                    )
                    if collection_exhausted:
                        break

                    self.pagination.advance_page()
                    self.cursor.page = self.pagination.current_page
                    self.cursor.slot_index = 0

                    if copies_in_batch >= max_copies_per_batch:
                        batch_full = True

                if not batch_cards:
                    break

                batch_num += 1
                lines = []
                for card in batch_cards:
                    set_part = f" ({card.set_code})" if card.set_code else ""
                    num_part = f" {card.collector_number}" if card.collector_number else ""
                    lines.append(f"{card.quantity} {card.name}{set_part}{num_part}")
                decklist_str = "\n".join(lines)

                logger.info(
                    "Exporting batch %d (%d card entries, %d total copies)...",
                    batch_num, len(batch_cards), copies_in_batch,
                )
                if not dry_run:
                    self.save_current_deck()
                    self.export_and_cleanup_deck(skip_search=not first_cycle)
                    BrowserController.open_privacy_browser()
                    tunnel_url = self.transfer_provider.get_url()
                    BrowserController.navigate_to_url(tunnel_url)
                    self.transfer_provider.transfer(decklist_str)
                    BrowserController.close_current_tab()

                exported_batches.append({
                    "batch_id": batch_num,
                    "cards": batch_cards,
                    "size": len(batch_cards),
                    "total_copies": copies_in_batch,
                    "status": "exported",
                    "exported_data": decklist_str,
                })
                first_cycle = False

            total_cards = self.state.get_total_cards()
            unique_cards = self.state.get_unique_cards_count()
            logger.info(
                "Collection scan completed: %d total cards (%d unique) across %d batches.",
                total_cards, unique_cards, len(exported_batches),
            )
            return exported_batches

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

    def save_current_deck(self) -> None:
        """Save the current deck, dismissing any 'Too Many Cards' warning popup if present."""
        logger.info("Saving current deck...")
        try:
            logger.info(
                "[SEQ:save_deck] Saving deck and dismissing 'Too Many Cards' popup if present."
            )
            MouseController.click(*get_click_point("save_deck_button"))
            sleep_random(0.5, 0.1, 0.2, 0.8)

            image = ScreenCapture.capture_screen()
            ok_btn = UIDetector.find_confirmation_ok_button(image)
            if ok_btn:
                x, y, w, h = ok_btn
                MouseController.click(x + w // 2, y + h // 2)
                sleep_random(0.3, 0.05, 0.1, 0.4)
            logger.info("Successfully saved current deck.")
        except Exception as e:
            logger.error(f"Failed to save current deck: {e}", exc_info=True)
            raise MTGARegistrarError(f"Failed to save current deck: {e}", details=str(e)) from e

    def export_and_cleanup_deck(self, skip_search: bool = False) -> None:
        """Search 'New Deck', select leftmost deck, export deck, delete deck, and confirm OK.

        Args:
            skip_search: If True, skip re-typing "New Deck" into the search bar,
                since the Decks screen search box retains its previous text across
                deck-builder sessions and only needs to be set once.
        """
        logger.info("Executing deck export and cleanup workflow...")
        try:
            logger.info(
                "[SEQ:export_cleanup] Search 'New Deck' -> select leftmost "
                "-> export -> delete -> confirm."
            )
            if not skip_search:
                image = ScreenCapture.capture_screen()

                search_bar = UIDetector.find_decks_search_bar(image)
                if search_bar:
                    x, y, w, h = search_bar
                    MouseController.click(x + w // 2, y + h // 2)
                else:
                    MouseController.click(*get_click_point("decks_search_bar"))
                sleep_random(0.2, 0.05, 0.1, 0.3)

                KeyboardController.hotkey("ctrl", "a")
                KeyboardController.type_text("New Deck", interval=0.04)
                KeyboardController.press_key("enter")
                sleep_random(0.8, 0.1, 0.3, 1.0)

            image = ScreenCapture.capture_screen()

            left_deck = UIDetector.find_leftmost_deck(image)
            if left_deck:
                x, y, w, h = left_deck
                MouseController.click(x + w // 2, y + h // 2)
            else:
                MouseController.click(*get_click_point("leftmost_deck_slot"))
            sleep_random(0.8, 0.1, 0.3, 1.0)

            image = ScreenCapture.capture_screen()

            export_btn = UIDetector.find_export_button(image)
            if export_btn:
                x, y, w, h = export_btn
                MouseController.click(x + w // 2, y + h // 2)
            else:
                MouseController.click(*get_click_point("export_deck_button"))
            sleep_random(0.8, 0.1, 0.3, 1.0)

            image = ScreenCapture.capture_screen()

            trash_btn = UIDetector.find_trash_can_button(image)
            if trash_btn:
                x, y, w, h = trash_btn
                MouseController.click(x + w // 2, y + h // 2)
            else:
                MouseController.click(*get_click_point("trash_can_button"))
            sleep_random(0.5, 0.1, 0.2, 0.8)

            image = ScreenCapture.capture_screen()

            ok_btn = UIDetector.find_confirmation_ok_button(image)
            if ok_btn:
                x, y, w, h = ok_btn
                MouseController.click(x + w // 2, y + h // 2)
            else:
                MouseController.click(*get_click_point("confirmation_ok_button"))
            sleep_random(0.8, 0.1, 0.3, 1.0)

            logger.info("Successfully completed deck export and cleanup workflow.")
        except Exception as e:
            logger.error(f"Deck export and cleanup failed: {e}", exc_info=True)
            raise MTGARegistrarError(f"Deck export and cleanup failed: {e}", details=str(e)) from e
