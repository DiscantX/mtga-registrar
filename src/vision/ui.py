"""UI element detection module for MTGA Registrar.

Provides detection for game navigation buttons (arrows), export options,
deck creation buttons, and format selectors (e.g., Timeless).
"""

import logging
from typing import Optional, Tuple

import numpy as np

from src.core.config import settings
from src.core.exceptions import VisionError
from src.vision.detector import TemplateDetector

logger = logging.getLogger("mtga_registrar.vision.ui")


class UIDetector:
    """Detects interactive UI elements in the MTGA application interface."""

    @staticmethod
    def find_navigation_button(
        image: np.ndarray,
        direction: str = "right",
        template: Optional[np.ndarray] = None,
        threshold: Optional[float] = None,
    ) -> Optional[Tuple[int, int, int, int]]:
        """Find navigation arrow buttons (left or right) for pagination.

        Args:
            image: BGR numpy array of the screen or navigation area.
            direction: Direction of navigation button ("left" or "right").
            template: Optional template image for the button.
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
                "No template for navigation button '%s', using heuristic",
                direction
            )
            h, w = image.shape[:2]
            if direction == "right":
                return (int(w * 0.85), int(h * 0.85), 60, 60)
            else:
                return (int(w * 0.10), int(h * 0.85), 60, 60)

        except Exception as e:
            logger.error(
                "Failed to find navigation button '%s': %s",
                direction, e, exc_info=True
            )
            raise VisionError(
                f"Navigation button detection failed: {e}", details=str(e)
            ) from e

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
            return (int(w * 0.25), int(h * 0.90), 120, 40)

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
            return (int(w * 0.15), int(h * 0.15), 140, 50)

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
            return (int(w * 0.50), int(h * 0.30), 160, 45)

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
            return (int(w * 0.70), int(h * 0.12), 200, 40)

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
            return (int(w * 0.15), int(h * 0.30), 180, 220)

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
            return (int(w * 0.85), int(h * 0.15), 50, 50)

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
            return (int(w * 0.55), int(h * 0.60), 120, 45)

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
            return (int(w * 0.50), int(h * 0.85), 220, 40)

        except Exception as e:
            logger.error("Failed to find privacy choices link: %s", e, exc_info=True)
            raise VisionError(
                f"Privacy choices link detection failed: {e}", details=str(e)
            ) from e
