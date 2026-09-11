"""Centralized registry of UI element locations for MTGA Registrar.

IMPORTANT: Every value in UI_LOCATIONS below is an UNVERIFIED PLACEHOLDER carried
over from earlier fabricated heuristics. None of these have been confirmed against
the real running MTGA client. Do not add new entries with invented numbers — new
entries must come from a human providing real calibrated values.
"""

import logging
from typing import Dict, Tuple

logger = logging.getLogger("mtga_registrar.core.ui_locations")


class UILocation:
    """A single named UI element location, expressed relative to screen size.

    Attributes:
        rel_x: Fraction (0.0-1.0) of screen width for the element's x position.
        rel_y: Fraction (0.0-1.0) of screen height for the element's y position.
        width_px: Fixed pixel width of the element's bounding box (0 if this
            location is a single click point rather than a box).
        height_px: Fixed pixel height of the element's bounding box (0 if this
            location is a single click point rather than a box).
        calibrated: True only once a human has confirmed this value against the
            real MTGA client. Must default to False for placeholder values.
    """

    def __init__(self, rel_x: float, rel_y: float, width_px: int, height_px: int, calibrated: bool):
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.width_px = width_px
        self.height_px = height_px
        self.calibrated = calibrated


UI_LOCATIONS: Dict[str, UILocation] = {
    "create_deck_button": UILocation(0.15, 0.15, 140, 50, False),
    "decks_search_bar": UILocation(0.70, 0.12, 200, 40, False),
    "leftmost_deck_slot": UILocation(0.15, 0.30, 180, 220, False),
    "export_deck_button": UILocation(0.25, 0.90, 120, 40, False),
    "trash_can_button": UILocation(0.85, 0.15, 50, 50, False),
    "confirmation_ok_button": UILocation(0.55, 0.60, 120, 45, False),
    "privacy_choices_link": UILocation(0.50, 0.85, 220, 40, False),
    "format_selector_dropdown": UILocation(0.50, 0.30, 160, 45, False),
    "pagination_nav_right": UILocation(0.85, 0.85, 60, 60, False),
    "pagination_nav_left": UILocation(0.10, 0.85, 60, 60, False),
    "save_deck_button_click": UILocation(0.9635, 0.0463, 0, 0, False),
    "fallback_search_bar_click": UILocation(0.7292, 0.1204, 0, 0, False),
    "fallback_leftmost_deck_click": UILocation(0.15625, 0.2778, 0, 0, False),
    "fallback_export_button_click": UILocation(0.2604, 0.8796, 0, 0, False),
    "fallback_trash_can_click": UILocation(0.8594, 0.1389, 0, 0, False),
    "fallback_confirm_ok_click": UILocation(0.5469, 0.6019, 0, 0, False),
    "fallback_privacy_choices_click": UILocation(0.5, 0.8333, 0, 0, False),
}


def get_location(name: str, screen_width: int, screen_height: int) -> Tuple[int, int, int, int]:
    """Resolve a named UI location to absolute pixel coordinates for a given screen size.

    Args:
        name: Key into UI_LOCATIONS.
        screen_width: Current screen width in pixels.
        screen_height: Current screen height in pixels.

    Returns:
        Tuple of (x, y, width, height) in absolute pixels.

    Raises:
        KeyError: If name is not a registered UI location.
    """
    loc = UI_LOCATIONS[name]
    if not loc.calibrated:
        logger.warning(
            "UI location '%s' is UNCALIBRATED (fabricated placeholder). "
            "Automation accuracy is not guaranteed at this coordinate.",
            name,
        )
    x = int(loc.rel_x * screen_width)
    y = int(loc.rel_y * screen_height)
    return (x, y, loc.width_px, loc.height_px)


def get_click_point(name: str) -> Tuple[int, int]:
    """Resolve a named UI location to an absolute (x, y) click point on the current screen.

    Uses `pyautogui.size()` to determine the current screen resolution.

    Args:
        name: Key into UI_LOCATIONS.

    Returns:
        Tuple of (x, y) absolute pixel coordinates.

    Raises:
        KeyError: If name is not a registered UI location.
    """
    import pyautogui  # type: ignore[import-untyped]

    screen_width, screen_height = pyautogui.size()
    x, y, _, _ = get_location(name, screen_width, screen_height)
    return (x, y)
