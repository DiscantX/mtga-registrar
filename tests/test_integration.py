"""Comprehensive integration tests for Phase 7: End-to-End Integration & Orchestration.

Verifies that initialization, deck creation, card scanning, pagination, batching,
and batch export operate cohesively without errors using mocks and simulation via
[`ApplicationController`](src/core/app.py).
"""

from typing import List

import pytest

from src.core.app import ApplicationController
from src.core.config import Settings
from src.core.exceptions import MTGARegistrarError
from src.core.state import CardEntry
from src.export.base import ClipboardTransferProvider


class MockTransferProvider(ClipboardTransferProvider):
    """Mock transfer provider for testing exports without modifying system clipboard."""

    def __init__(self) -> None:
        self.transferred_data: List[str] = []
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def transfer(self, data: str) -> bool:
        self.transferred_data.append(data)
        return True

    def get_url(self) -> str:
        return "https://mock.tunnelmole.net"


def test_end_to_end_workflow_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify successful end-to-end collection export workflow across multiple pages."""
    monkeypatch.setattr(
        "src.vision.capture.ScreenCapture.capture_screen", lambda: None
    )
    monkeypatch.setattr(
        "src.automation.mouse.MouseController.click", lambda x, y: None
    )
    monkeypatch.setattr(
        "src.automation.mouse.MouseController.scroll_down", lambda clicks=1: None
    )
    monkeypatch.setattr(
        "src.automation.keyboard.KeyboardController.hotkey",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "src.automation.keyboard.KeyboardController.type_text",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "src.automation.keyboard.KeyboardController.press_key",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "src.vision.ui.UIDetector.find_confirmation_ok_button",
        lambda img: (0, 0, 10, 10),
    )
    monkeypatch.setattr(
        "src.vision.ui.UIDetector.find_decks_search_bar",
        lambda img: (0, 0, 10, 10),
    )
    monkeypatch.setattr(
        "src.vision.ui.UIDetector.find_leftmost_deck",
        lambda img: (0, 0, 10, 10),
    )
    monkeypatch.setattr(
        "src.vision.ui.UIDetector.find_export_button",
        lambda img: (0, 0, 10, 10),
    )
    monkeypatch.setattr(
        "src.vision.ui.UIDetector.find_trash_can_button",
        lambda img: (0, 0, 10, 10),
    )

    transfer_provider = MockTransferProvider()
    settings = Settings(max_batch_size=10, log_level="DEBUG")
    controller = ApplicationController(
        config=settings, transfer_provider=transfer_provider
    )

    def page_scanner(page_num: int) -> List[CardEntry]:
        if page_num == 0:
            return [
                CardEntry(
                    name="Lightning Bolt",
                    quantity=4,
                    set_code="STA",
                    collector_number="42",
                ),
                CardEntry(
                    name="Counterspell",
                    quantity=4,
                    set_code="STA",
                    collector_number="15",
                ),
            ]
        elif page_num == 1:
            return [
                CardEntry(
                    name="Dark Ritual",
                    quantity=4,
                    set_code="STA",
                    collector_number="26",
                ),
            ]
        else:
            return []  # End of collection (empty page)

    batches = controller.export_collection(
        dry_run=False, page_scanner=page_scanner
    )

    assert transfer_provider.started is True
    assert transfer_provider.stopped is True
    assert len(batches) >= 1
    assert controller.state.get_total_cards() == 12  # 4 + 4 + 4
    assert controller.state.get_unique_cards_count() == 3
    assert len(transfer_provider.transferred_data) > 0


def test_end_to_end_workflow_dry_run() -> None:
    """Verify end-to-end export workflow in dry-run mode (no transfer calls)."""
    transfer_provider = MockTransferProvider()
    controller = ApplicationController(transfer_provider=transfer_provider)

    def page_scanner(page_num: int) -> List[CardEntry]:
        if page_num == 0:
            return [CardEntry(name="Island", quantity=4)]
        return []

    batches = controller.export_collection(
        dry_run=True, page_scanner=page_scanner
    )

    assert transfer_provider.started is True
    assert transfer_provider.stopped is True
    # In dry_run=True, transfer() should not be called
    assert len(transfer_provider.transferred_data) == 0
    assert len(batches) == 1
    assert batches[0]["size"] == 1
    assert batches[0]["cards"][0].quantity == 4


def test_deck_creation_failure() -> None:
    """Verify that deck creation failure raises MTGARegistrarError."""
    controller = ApplicationController()

    def bad_nav() -> bool:
        return False

    with pytest.raises(MTGARegistrarError):
        controller.create_deck(nav_callback=bad_nav)


def test_large_collection_batching(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify batching and export of a large collection (> max_batch_size)."""
    monkeypatch.setattr(
        "src.vision.capture.ScreenCapture.capture_screen", lambda: None
    )
    monkeypatch.setattr(
        "src.automation.mouse.MouseController.click", lambda x, y: None
    )
    monkeypatch.setattr(
        "src.automation.mouse.MouseController.scroll_down", lambda clicks=1: None
    )
    monkeypatch.setattr(
        "src.automation.keyboard.KeyboardController.hotkey",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "src.automation.keyboard.KeyboardController.type_text",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "src.automation.keyboard.KeyboardController.press_key",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "src.vision.ui.UIDetector.find_confirmation_ok_button",
        lambda img: (0, 0, 10, 10),
    )
    monkeypatch.setattr(
        "src.vision.ui.UIDetector.find_decks_search_bar",
        lambda img: (0, 0, 10, 10),
    )
    monkeypatch.setattr(
        "src.vision.ui.UIDetector.find_leftmost_deck",
        lambda img: (0, 0, 10, 10),
    )
    monkeypatch.setattr(
        "src.vision.ui.UIDetector.find_export_button",
        lambda img: (0, 0, 10, 10),
    )
    monkeypatch.setattr(
        "src.vision.ui.UIDetector.find_trash_can_button",
        lambda img: (0, 0, 10, 10),
    )

    transfer_provider = MockTransferProvider()
    settings = Settings(max_batch_size=50)
    controller = ApplicationController(
        config=settings, transfer_provider=transfer_provider
    )

    def page_scanner(page_num: int) -> List[CardEntry]:
        if page_num == 0:
            return [
                CardEntry(
                    name=f"Card {i}",
                    quantity=1,
                    set_code="TST",
                    collector_number=str(i),
                )
                for i in range(70)
            ]
        elif page_num == 1:
            return [
                CardEntry(
                    name=f"Card {i}",
                    quantity=1,
                    set_code="TST",
                    collector_number=str(i),
                )
                for i in range(70, 120)
            ]
        return []

    batches = controller.export_collection(
        dry_run=False, page_scanner=page_scanner
    )

    # 120 unique cards with max_batch_size=50 -> 3 batches (50, 50, 20)
    assert len(batches) == 3
    assert batches[0]["size"] == 50
    assert batches[1]["size"] == 50
    assert batches[2]["size"] == 20
    assert len(transfer_provider.transferred_data) == 3


def test_deck_save_and_cleanup_orchestration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify deck save and cleanup execution steps with mocked automation/vision."""
    controller = ApplicationController()

    monkeypatch.setattr(
        "src.vision.capture.ScreenCapture.capture_screen", lambda: None
    )
    monkeypatch.setattr(
        "src.automation.mouse.MouseController.click", lambda x, y: None
    )
    monkeypatch.setattr(
        "src.automation.keyboard.KeyboardController.hotkey",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "src.automation.keyboard.KeyboardController.type_text",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "src.automation.keyboard.KeyboardController.press_key",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "src.vision.ui.UIDetector.find_confirmation_ok_button",
        lambda img: (0, 0, 10, 10),
    )
    monkeypatch.setattr(
        "src.vision.ui.UIDetector.find_decks_search_bar",
        lambda img: (0, 0, 10, 10),
    )
    monkeypatch.setattr(
        "src.vision.ui.UIDetector.find_leftmost_deck",
        lambda img: (0, 0, 10, 10),
    )
    monkeypatch.setattr(
        "src.vision.ui.UIDetector.find_export_button",
        lambda img: (0, 0, 10, 10),
    )
    monkeypatch.setattr(
        "src.vision.ui.UIDetector.find_trash_can_button",
        lambda img: (0, 0, 10, 10),
    )

    controller.save_current_deck()
    controller.export_and_cleanup_deck()

