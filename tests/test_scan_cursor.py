"""Unit tests for resumable, copy-limit-aware batch scanning."""

from typing import List

from src.core.app import ApplicationController
from src.core.config import Settings
from src.core.state import CardEntry
from src.export.base import ClipboardTransferProvider


class MockTransferProvider(ClipboardTransferProvider):
    """Mock transfer provider for testing exports without touching the system clipboard."""

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


def test_partial_card_resumes_across_batches() -> None:
    """Verify a card whose owned quantity exceeds the remaining batch capacity is
    split correctly across two batches and the full quantity ends up in state."""
    transfer_provider = MockTransferProvider()
    settings = Settings(max_batch_size=3)
    controller = ApplicationController(config=settings, transfer_provider=transfer_provider)

    def page_scanner(page_num: int) -> List[CardEntry]:
        if page_num == 0:
            return [CardEntry(name="Forest", quantity=4, set_code="FIN", collector_number="306")]
        return []

    batches = controller.export_collection(dry_run=True, page_scanner=page_scanner)

    assert len(batches) == 2
    assert batches[0]["total_copies"] == 3
    assert batches[1]["total_copies"] == 1
    assert batches[0]["cards"][0].name == "Forest"
    assert batches[0]["cards"][0].quantity == 3
    assert batches[1]["cards"][0].quantity == 1
    assert controller.state.get_total_cards() == 4
    assert controller.state.get_unique_cards_count() == 1


def test_scan_cursor_resets_between_runs() -> None:
    """Verify the cursor is fully reset at the start of export_collection."""
    transfer_provider = MockTransferProvider()
    controller = ApplicationController(transfer_provider=transfer_provider)
    controller.pagination.consecutive_empty_limit = 1
    controller.cursor.page = 5
    controller.cursor.slot_index = 3

    def page_scanner(page_num: int) -> List[CardEntry]:
        return []

    controller.export_collection(dry_run=True, page_scanner=page_scanner)

    assert controller.cursor.page == 0
    assert controller.cursor.slot_index == 0
    assert controller.cursor.partial_card is None
