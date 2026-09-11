"""Comprehensive unit tests for Phase 4: State Management & Pagination Logic.

Verifies state tracking, card entries, pagination advancement, scroll loops,
and batch chunking at the 250-card threshold.
"""

import pytest

from src.core.batching import BatchController
from src.core.exceptions import StateError
from src.core.pagination import PaginationManager
from src.core.state import CardEntry, CollectionState


def test_card_entry_valid() -> None:
    """Verify CardEntry initialization and unique_id generation."""
    entry = CardEntry(
        name="Llanowar Elves",
        quantity=2,
        set_code="FDN",
        collector_number="227",
    )
    assert entry.name == "Llanowar Elves"
    assert entry.quantity == 2
    assert entry.set_code == "FDN"
    assert entry.collector_number == "227"
    assert entry.unique_id == "llanowar elves_fdn_227"


def test_card_entry_invalid_name() -> None:
    """Verify CardEntry raises StateError on empty name."""
    with pytest.raises(StateError):
        CardEntry(name="   ", quantity=1)


def test_card_entry_invalid_quantity() -> None:
    """Verify CardEntry raises StateError on non-positive quantity."""
    with pytest.raises(StateError):
        CardEntry(name="Forest", quantity=0)


def test_collection_state_management() -> None:
    """Verify CollectionState tracking, card addition, deduplication/accumulation."""
    state = CollectionState()
    assert state.get_total_cards() == 0
    assert state.get_unique_cards_count() == 0

    # Add first card
    entry1 = state.add_card(
        name="Forest",
        quantity=4,
        set_code="FIN",
        collector_number="306",
    )
    assert state.get_unique_cards_count() == 1
    assert state.get_total_cards() == 4
    assert state.has_seen(entry1.unique_id) is True
    assert state.get_card_count(entry1.unique_id) == 4

    # Add duplicate card (should accumulate quantity)
    entry2 = state.add_card(
        name="Forest",
        quantity=2,
        set_code="FIN",
        collector_number="306",
    )
    assert entry2.unique_id == entry1.unique_id
    assert state.get_unique_cards_count() == 1
    assert state.get_total_cards() == 6
    assert state.get_card_count(entry1.unique_id) == 6

    # Add another distinct card
    state.add_card(
        name="Llanowar Elves",
        quantity=2,
        set_code="FDN",
        collector_number="227",
    )
    assert state.get_unique_cards_count() == 2
    assert state.get_total_cards() == 8

    stats = state.get_statistics()
    assert stats["total_cards"] == 8
    assert stats["unique_cards"] == 2

    # Reset
    state.reset()
    assert state.get_total_cards() == 0
    assert state.get_unique_cards_count() == 0


def test_pagination_manager() -> None:
    """Verify pagination advancement and end-of-collection detection."""
    paginator = PaginationManager(max_pages=3, consecutive_empty_limit=2)
    assert paginator.current_page == 0

    # Advance page successfully
    success = paginator.advance_page()
    assert success is True
    assert paginator.current_page == 1

    # Advance with custom navigation callback
    nav_called = []

    def custom_nav() -> bool:
        nav_called.append(True)
        return True

    success = paginator.advance_page(navigate_func=custom_nav)
    assert success is True
    assert len(nav_called) == 1
    assert paginator.current_page == 2

    # Test end of collection detection by empty cards
    assert paginator.check_end_of_collection(new_cards_found_count=0) is False
    assert (
        paginator.check_end_of_collection(new_cards_found_count=0) is True
    )  # Reached empty limit (2)

    # Test reset
    paginator.reset()
    assert paginator.current_page == 0

    # Test max pages limit
    paginator.current_page = 3
    with pytest.raises(StateError):
        paginator.advance_page()


def test_batch_controller_threshold() -> None:
    """Verify batch chunking at the 250-card threshold."""
    controller = BatchController(max_batch_size=250)
    assert controller.max_batch_size == 250

    # Create 300 dummy cards (e.g. CardEntry objects)
    cards = [
        CardEntry(
            name=f"Card {i}",
            quantity=1,
            set_code="TST",
            collector_number=str(i),
        )
        for i in range(300)
    ]

    batches = controller.create_batches(cards)
    assert len(batches) == 2
    assert batches[0]["size"] == 250
    assert batches[1]["size"] == 50
    assert batches[0]["status"] == "pending"

    pending = controller.get_pending_batches()
    assert len(pending) == 2

    # Mark first batch exported
    controller.mark_batch_exported(1)
    assert len(controller.get_pending_batches()) == 1
    assert controller.get_batches()[0]["status"] == "exported"

    # Invalid batch ID
    with pytest.raises(StateError):
        controller.mark_batch_exported(999)

    # Invalid chunk input
    with pytest.raises(StateError):
        controller.chunk_cards("not a list")  # type: ignore

    # Reset
    controller.reset()
    assert len(controller.get_batches()) == 0
