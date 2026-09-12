"""UI element detection module for MTGA Registrar.

Provides detection for game navigation buttons, export options,
deck creation buttons, and format selectors (e.g., Timeless).

All UI element positions are resolved from `src/core/ui_locations.py`'s
calibrated registry. Template matching is not used for any of these
elements — only the card ownership diamond and infinity indicators in
`src/vision/detector.py` use template matching, since those require actual
visual identification rather than a fixed screen position.
"""

import logging
from typing import Optional, Tuple

import numpy as np

from src.core.config import settings
from src.core.exceptions import VisionError
from src.core.ui_locations import detect_aspect_ratio, get_location
from src.vision.detector import TemplateDetector

logger = logging.getLogger("mtga_registrar.vision.ui")


class UIDetector:
    """Detects interactive UI elements in the MTGA application interface."""

    @staticmethod
    def find_export_button(
        image: np.ndarray,
        template: Optional[np.ndarray] = None,
        threshold: Optional[float] = None,
    ) -> Optional[Tuple[int, int, int, int]]:
        """Find the deck export / copy to clipboard button.

        Args:
            image: BGR numpy array of the deck builder interface.
            template: Optional template image of the export button.
            threshold: Optional confidence threshold.

        Returns:
            Bounding box tuple (x, y, width, height) if found, else None.
        """
        thresh = threshold or settings.confidence_threshold
        try:
            if template is not None:
                matches = TemplateDetector.match_template(
                    image, template, threshold=thresh
                )
                if matches:
                    best = max(matches, key=lambda m: m[4])
                    return (best[0], best[1], best[2], best[3])

            logger.debug("No template for export button, using heuristic")
            h, w = image.shape[:2]
            aspect_ratio = detect_aspect_ratio(w, h)
            return get_location("export_deck_button", w, h, aspect_ratio)

        except Exception as e:
            logger.error("Failed to find export button: %s", e, exc_info=True)
            raise VisionError(
                f"Export button detection failed: {e}", details=str(e)
            ) from e

    @staticmethod
    def find_deck_creation_button(
        image: np.ndarray,
        template: Optional[np.ndarray] = None,
        threshold: Optional[float] = None,
    ) -> Optional[Tuple[int, int, int, int]]:
        """Find the 'Create Deck' button in the decks menu.

        Args:
            image: BGR numpy array of the decks screen.
            template: Optional template image.
            threshold: Optional confidence threshold.

        Returns:
            Bounding box tuple (x, y, width, height) if found, else None.
        """
        thresh = threshold or settings.confidence_threshold
        try:
            if template is not None:
                matches = TemplateDetector.match_template(
                    image, template, threshold=thresh
                )
                if matches:
                    best = max(matches, key=lambda m: m[4])
                    return (best[0], best[1], best[2], best[3])

            logger.debug("No template for deck creation button, heuristic")
            h, w = image.shape[:2]
            aspect_ratio = detect_aspect_ratio(w, h)
            return get_location("create_deck_button", w, h, aspect_ratio)

        except Exception as e:
            logger.error(
                "Failed to find deck creation button: %s", e, exc_info=True
            )
            raise VisionError(
                f"Deck creation button detection failed: {e}", details=str(e)
            ) from e

    @staticmethod
    def find_format_selector(
        image: np.ndarray,
        format_name: str = "Timeless",
        template: Optional[np.ndarray] = None,
        threshold: Optional[float] = None,
    ) -> Optional[Tuple[int, int, int, int]]:
        """Find format selector button or dropdown (e.g., 'Timeless').

        Args:
            image: BGR numpy array of the deck creation screen.
            format_name: Name of the format (default "Timeless").
            template: Optional template image.
            threshold: Optional confidence threshold.

        Returns:
            Bounding box tuple (x, y, width, height) if found, else None.
        """
        thresh = threshold or settings.confidence_threshold
        try:
            if template is not None:
                matches = TemplateDetector.match_template(
                    image, template, threshold=thresh
                )
                if matches:
                    best = max(matches, key=lambda m: m[4])
                    return (best[0], best[1], best[2], best[3])

            logger.debug(
                "No template for format '%s', using heuristic", format_name
            )
            h, w = image.shape[:2]
            aspect_ratio = detect_aspect_ratio(w, h)
            return get_location("format_selector_dropdown", w, h, aspect_ratio)

        except Exception as e:
            logger.error(
                "Failed format selector for '%s': %s",
                format_name, e, exc_info=True
            )
            raise VisionError(
                f"Format selector detection failed: {e}", details=str(e)
            ) from e

    @staticmethod
    def find_decks_search_bar(
        image: np.ndarray,
        template: Optional[np.ndarray] = None,
        threshold: Optional[float] = None,
    ) -> Optional[Tuple[int, int, int, int]]:
        """Find the search bar in the Decks screen.

        Args:
            image: BGR numpy array of the decks screen.
            template: Optional template image.
            threshold: Optional confidence threshold.

        Returns:
            Bounding box tuple (x, y, width, height) if found, else None.
        """
        thresh = threshold or settings.confidence_threshold
        try:
            if template is not None:
                matches = TemplateDetector.match_template(
                    image, template, threshold=thresh
                )
                if matches:
                    best = max(matches, key=lambda m: m[4])
                    return (best[0], best[1], best[2], best[3])

            logger.debug("No template for decks search bar, using heuristic")
            h, w = image.shape[:2]
            aspect_ratio = detect_aspect_ratio(w, h)
            return get_location("decks_search_bar", w, h, aspect_ratio)

        except Exception as e:
            logger.error("Failed to find decks search bar: %s", e, exc_info=True)
            raise VisionError(
                f"Decks search bar detection failed: {e}", details=str(e)
            ) from e

    @staticmethod
    def find_leftmost_deck(
        image: np.ndarray,
        template: Optional[np.ndarray] = None,
        threshold: Optional[float] = None,
    ) -> Optional[Tuple[int, int, int, int]]:
        """Find the leftmost (newest) deck card slot in the Decks screen.

        Args:
            image: BGR numpy array of the decks screen.
            template: Optional template image.
            threshold: Optional confidence threshold.

        Returns:
            Bounding box tuple (x, y, width, height) if found, else None.
        """
        thresh = threshold or settings.confidence_threshold
        try:
            if template is not None:
                matches = TemplateDetector.match_template(
                    image, template, threshold=thresh
                )
                if matches:
                    best = max(matches, key=lambda m: m[4])
                    return (best[0], best[1], best[2], best[3])

            logger.debug("No template for leftmost deck, using heuristic")
            h, w = image.shape[:2]
            aspect_ratio = detect_aspect_ratio(w, h)
            return get_location("leftmost_deck_slot", w, h, aspect_ratio)

        except Exception as e:
            logger.error("Failed to find leftmost deck: %s", e, exc_info=True)
            raise VisionError(
                f"Leftmost deck detection failed: {e}", details=str(e)
            ) from e

    @staticmethod
    def find_trash_can_button(
        image: np.ndarray,
        template: Optional[np.ndarray] = None,
        threshold: Optional[float] = None,
    ) -> Optional[Tuple[int, int, int, int]]:
        """Find the delete (trash can) button for a selected deck.

        Args:
            image: BGR numpy array of the deck details/edit screen.
            template: Optional template image.
            threshold: Optional confidence threshold.

        Returns:
            Bounding box tuple (x, y, width, height) if found, else None.
        """
        thresh = threshold or settings.confidence_threshold
        try:
            if template is not None:
                matches = TemplateDetector.match_template(
                    image, template, threshold=thresh
                )
                if matches:
                    best = max(matches, key=lambda m: m[4])
                    return (best[0], best[1], best[2], best[3])

            logger.debug("No template for trash can button, using heuristic")
            h, w = image.shape[:2]
            aspect_ratio = detect_aspect_ratio(w, h)
            return get_location("trash_can_button", w, h, aspect_ratio)

        except Exception as e:
            logger.error("Failed to find trash can button: %s", e, exc_info=True)
            raise VisionError(
                f"Trash can button detection failed: {e}", details=str(e)
            ) from e

    @staticmethod
    def find_confirmation_ok_button(
        image: np.ndarray,
        template: Optional[np.ndarray] = None,
        threshold: Optional[float] = None,
    ) -> Optional[Tuple[int, int, int, int]]:
        """Find the confirmation 'OK' dialogue button.

        Args:
            image: BGR numpy array of the confirmation dialog popup.
            template: Optional template image.
            threshold: Optional confidence threshold.

        Returns:
            Bounding box tuple (x, y, width, height) if found, else None.
        """
        thresh = threshold or settings.confidence_threshold
        try:
            if template is not None:
                matches = TemplateDetector.match_template(
                    image, template, threshold=thresh
                )
                if matches:
                    best = max(matches, key=lambda m: m[4])
                    return (best[0], best[1], best[2], best[3])

            logger.debug("No template for confirmation OK button, using heuristic")
            h, w = image.shape[:2]
            aspect_ratio = detect_aspect_ratio(w, h)
            return get_location("confirmation_ok_button", w, h, aspect_ratio)

        except Exception as e:
            logger.error("Failed to find confirmation OK button: %s", e, exc_info=True)
            raise VisionError(
                f"Confirmation OK button detection failed: {e}", details=str(e)
            ) from e

    @staticmethod
    def find_privacy_choices_link(
        image: np.ndarray,
        template: Optional[np.ndarray] = None,
        threshold: Optional[float] = None,
    ) -> Optional[Tuple[int, int, int, int]]:
        """Find the 'Your Privacy Choices' link in the escape menu / browser.

        Args:
            image: BGR numpy array of the escape menu.
            template: Optional template image.
            threshold: Optional confidence threshold.

        Returns:
            Bounding box tuple (x, y, width, height) if found, else None.
        """
        thresh = threshold or settings.confidence_threshold
        try:
            if template is not None:
                matches = TemplateDetector.match_template(
                    image, template, threshold=thresh
                )
                if matches:
                    best = max(matches, key=lambda m: m[4])
                    return (best[0], best[1], best[2], best[3])

            logger.debug("No template for privacy choices link, using heuristic")
            h, w = image.shape[:2]
            aspect_ratio = detect_aspect_ratio(w, h)
            return get_location("privacy_choices_link", w, h, aspect_ratio)

        except Exception as e:
            logger.error("Failed to find privacy choices link: %s", e, exc_info=True)
            raise VisionError(
                f"Privacy choices link detection failed: {e}", details=str(e)
            ) from e
