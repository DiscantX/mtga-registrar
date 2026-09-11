"""MTGA decklist export parser module.

This module provides data models (`CardModel`, `DeckModel`) and robust parsing
utilities to convert raw MTGA clipboard / export text into structured Python objects
and JSON representations.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.core.exceptions import ExportError

logger = logging.getLogger("mtga_registrar.export.parser")


@dataclass
class CardModel:
    """Represents an individual card parsed from an MTGA deck export.

    Attributes:
        quantity: Number of copies of the card.
        name: Name of the card.
        set_code: Optional set code (e.g., 'FDN', 'FIN', 'BLB').
        collector_number: Optional collector number (e.g., '227', '306').
        category: Section category ('mainboard', 'sideboard', etc.).
    """

    quantity: int
    name: str
    set_code: Optional[str] = None
    collector_number: Optional[str] = None
    category: str = "mainboard"

    def to_dict(self) -> Dict[str, Any]:
        """Convert card model to a dictionary representation.

        Returns:
            Dictionary of card attributes.
        """
        return {
            "quantity": self.quantity,
            "name": self.name,
            "set_code": self.set_code,
            "collector_number": self.collector_number,
            "category": self.category,
        }


@dataclass
class DeckModel:
    """Represents a parsed MTGA deck with mainboard and optional sideboard cards.

    Attributes:
        name: Optional name of the deck.
        cards: List of CardModel items.
    """

    name: Optional[str] = None
    cards: List[CardModel] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert deck model to a dictionary representation.

        Returns:
            Dictionary containing deck name and cards list.
        """
        return {
            "name": self.name,
            "cards": [card.to_dict() for card in self.cards],
            "total_cards": sum(c.quantity for c in self.cards),
            "unique_cards": len(self.cards),
        }

    def to_json(self) -> str:
        """Convert deck model to a JSON string.

        Returns:
            JSON formatted string representation of the deck.
        """
        return json.dumps(self.to_dict(), indent=2)


class DeckParser:
    """Parser for MTGA deck export clipboard text."""

    # Regex for MTGA card line format:
    # e.g., "2 Llanowar Elves (FDN) 227" or "4 Lightning Bolt"
    CARD_PATTERN = re.compile(
        r"^(\d+)\s+(.+?)(?:\s+\(([A-Z0-9]+)\)\s+([0-9a-zA-Z]+))?\s*$"
    )

    @classmethod
    def parse(cls, text: str) -> DeckModel:
        """Parse raw MTGA export text into a structured DeckModel.

        Args:
            text: Raw multiline text string from MTGA clipboard export.

        Returns:
            Structured DeckModel object containing parsed cards.

        Raises:
            ExportError: If text is invalid or parsing fails critically.
        """
        if not isinstance(text, str):
            raise ExportError("Deck export text must be a string.")

        deck = DeckModel(name=None)
        current_category = "mainboard"
        lines = text.strip().splitlines()

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            # Check for section headers (e.g. "Deck", "Sideboard", or deck name)
            lower_line = stripped.lower()
            if lower_line in ("deck", "mainboard"):
                current_category = "mainboard"
                continue
            elif lower_line == "sideboard":
                current_category = "sideboard"
                continue
            elif deck.name is None and not cls.CARD_PATTERN.match(stripped):
                # First non-card, non-header line is often the deck name
                deck.name = stripped
                continue

            # Match card line
            match = cls.CARD_PATTERN.match(stripped)
            if match:
                qty_str, name_str, set_code, collector_num = match.groups()
                try:
                    quantity = int(qty_str)
                except ValueError:
                    logger.warning(
                        "Invalid quantity '%s' at line %d: %s",
                        qty_str,
                        line_num,
                        stripped,
                    )
                    continue

                card = CardModel(
                    quantity=quantity,
                    name=name_str.strip(),
                    set_code=set_code.strip() if set_code else None,
                    collector_number=(
                        collector_num.strip() if collector_num else None
                    ),
                    category=current_category,
                )
                deck.cards.append(card)
            else:
                logger.debug(
                    "Skipping unparseable line %d: '%s'", line_num, stripped
                )

        logger.info(
            "Successfully parsed deck '%s' with %d card entries (%d total cards).",
            deck.name or "Unnamed Deck",
            len(deck.cards),
            sum(c.quantity for c in deck.cards),
        )
        return deck
