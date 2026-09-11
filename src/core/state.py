"""Collection state tracking module for MTGA Registrar.

This module provides state management for tracking processed cards, quantities,
unique card identifiers, and overall collection progress during export.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.core.exceptions import StateError

logger = logging.getLogger("mtga_registrar.core.state")


@dataclass
class CardEntry:
    """Represents a card entry in the collection state.

    Attributes:
        name: Name of the card.
        quantity: Quantity owned or counted.
        set_code: Optional set code (e.g., 'ONE', 'MID').
        collector_number: Optional collector number.
        unique_id: Unique identifier for deduplication.
    """

    name: str
    quantity: int = 1
    set_code: Optional[str] = None
    collector_number: Optional[str] = None
    unique_id: str = field(default="")

    def __post_init__(self) -> None:
        """Initialize unique_id if not provided."""
        if not self.name or not self.name.strip():
            raise StateError("Card name cannot be empty")
        if self.quantity <= 0:
            raise StateError(
                f"Card quantity must be positive, got {self.quantity}"
            )

        if not self.unique_id:
            normalized_name = self.name.strip().lower()
            set_str = (self.set_code or "").strip().lower()
            num_str = (self.collector_number or "").strip().lower()
            self.unique_id = f"{normalized_name}_{set_str}_{num_str}"


class CollectionState:
    """Manages the state of collected cards during the export workflow."""

    def __init__(self) -> None:
        """Initialize empty collection state."""
        self._cards: Dict[str, CardEntry] = {}
        self._seen_ids: set[str] = set()
        logger.debug("Initialized empty CollectionState")

    def add_card(
        self,
        name: str,
        quantity: int = 1,
        set_code: Optional[str] = None,
        collector_number: Optional[str] = None,
        unique_id: Optional[str] = None,
    ) -> CardEntry:
        """Add or update a card in the collection state.

        Args:
            name: Card name.
            quantity: Quantity to add (default 1).
            set_code: Optional set code.
            collector_number: Optional collector number.
            unique_id: Optional custom unique identifier.

        Returns:
            The CardEntry added or updated.

        Raises:
            StateError: If parameters are invalid.
        """
        try:
            temp_entry = CardEntry(
                name=name,
                quantity=quantity,
                set_code=set_code,
                collector_number=collector_number,
                unique_id=unique_id or "",
            )
        except Exception as e:
            if isinstance(e, StateError):
                raise
            raise StateError(
                f"Failed to create card entry: {e}", details=str(e)
            ) from e

        uid = temp_entry.unique_id

        if uid in self._cards:
            existing = self._cards[uid]
            existing.quantity += temp_entry.quantity
            logger.debug(
                "Updated existing card '%s' quantity to %d",
                existing.name,
                existing.quantity,
            )
            entry = existing
        else:
            self._cards[uid] = temp_entry
            self._seen_ids.add(uid)
            logger.debug(
                "Added new card '%s' (ID: %s, Qty: %d)",
                temp_entry.name,
                uid,
                temp_entry.quantity,
            )
            entry = temp_entry

        return entry

    def has_seen(self, unique_id: str) -> bool:
        """Check if a card with the given unique identifier has been seen.

        Args:
            unique_id: Unique card identifier.

        Returns:
            True if seen, False otherwise.
        """
        return unique_id in self._seen_ids

    def get_card_count(self, unique_id: str) -> int:
        """Get the quantity of a specific card by unique identifier.

        Args:
            unique_id: Unique card identifier.

        Returns:
            Quantity owned, or 0 if not found.
        """
        if unique_id in self._cards:
            return self._cards[unique_id].quantity
        return 0

    def get_total_cards(self) -> int:
        """Get total quantity of all cards in the collection.

        Returns:
            Sum of all card quantities.
        """
        return sum(card.quantity for card in self._cards.values())

    def get_unique_cards_count(self) -> int:
        """Get the number of unique cards in the collection.

        Returns:
            Count of unique card entries.
        """
        return len(self._cards)

    def get_all_cards(self) -> List[CardEntry]:
        """Retrieve all card entries in the collection state.

        Returns:
            List of all CardEntry objects.
        """
        return list(self._cards.values())

    def get_statistics(self) -> Dict[str, Any]:
        """Get summary statistics of the collection state.

        Returns:
            Dictionary containing total cards, unique cards, and batch count estimates.
        """
        return {
            "total_cards": self.get_total_cards(),
            "unique_cards": self.get_unique_cards_count(),
        }

    def reset(self) -> None:
        """Reset collection state, clearing all cards and seen identifiers."""
        self._cards.clear()
        self._seen_ids.clear()
        logger.debug("Reset CollectionState")
