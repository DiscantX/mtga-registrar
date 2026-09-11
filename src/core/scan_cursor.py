"""Scan cursor tracking for resumable, batch-aware collection scanning.

The MTGA collection view always resets to page 1 whenever a new deck is created,
and the in-game 250-card deck limit is enforced on save (as total copies, not
unique cards). This module tracks exactly where scanning left off (page + slot)
and any partially-added card, so a fresh deck-builder session can resume from the
exact same spot instead of re-scanning from the start or losing track of a card
that was only half-clicked when the limit was hit.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PartialCard:
    """A card that was only partially clicked before the batch copy limit was hit.

    Attributes:
        name: Card name.
        set_code: Optional set code.
        collector_number: Optional collector number.
        unique_id: Unique identifier matching CollectionState's dedup key, so the
            remaining copies accumulate onto the same CardEntry.
        remaining_qty: Number of additional copies still owed to this card in the
            next batch session.
    """

    name: str
    set_code: Optional[str]
    collector_number: Optional[str]
    unique_id: str
    remaining_qty: int


@dataclass
class ScanCursor:
    """Tracks scan resume position across deck-builder sessions.

    Attributes:
        page: Zero-based collection page index to resume scanning from.
        slot_index: Zero-based index into that page's slot list, marking the
            first slot not yet fully processed.
        partial_card: If set, this card must have `remaining_qty` copies
            clicked at `slot_index` before continuing to scan later slots.
    """

    page: int = 0
    slot_index: int = 0
    partial_card: Optional[PartialCard] = None

    def reset(self) -> None:
        """Reset the cursor to the very start of the collection."""
        self.page = 0
        self.slot_index = 0
        self.partial_card = None
