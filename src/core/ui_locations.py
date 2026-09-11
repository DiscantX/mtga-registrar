"""Centralized registry of UI element locations for MTGA Registrar.

Supports aspect-ratio specific location mappings (16:10 and 16:9).
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


# 16:10 Aspect Ratio UI Registry (Calibrated from 16:10 screenshots)
UI_LOCATIONS_16_10: Dict[str, UILocation] = {
    "create_deck_button": UILocation(0.108, 0.421, 307, 260, True),
    "decks_search_bar": UILocation(0.233, 0.125, 460, 40, True),
    "leftmost_deck_slot": UILocation(0.278, 0.421, 307, 260, True),
    "export_deck_button": UILocation(0.330, 0.930, 40, 40, True),
    "trash_can_button": UILocation(0.435, 0.930, 40, 40, True),
    "confirmation_ok_button": UILocation(0.547, 0.602, 120, 45, True),
    "privacy_choices_link": UILocation(0.500, 0.833, 220, 40, True),
    "format_selector_dropdown": UILocation(0.900, 0.127, 200, 45, True),
    "save_deck_button": UILocation(0.892, 0.930, 180, 50, True),
    "pagination_nav_right": UILocation(0.742, 0.588, 40, 60, True),
    "pagination_nav_left": UILocation(0.042, 0.680, 40, 60, True),
}

# 16:9 Aspect Ratio UI Registry (Placeholder / Uncalibrated)
UI_LOCATIONS_16_9: Dict[str, UILocation] = {
    "create_deck_button": UILocation(0.15, 0.15, 140, 50, False),
    "decks_search_bar": UILocation(0.70, 0.12, 200, 40, False),
    "leftmost_deck_slot": UILocation(0.15, 0.30, 180, 220, False),
    "export_deck_button": UILocation(0.25, 0.90, 120, 40, False),
    "trash_can_button": UILocation(0.85, 0.15, 50, 50, False),
    "confirmation_ok_button": UILocation(0.55, 0.60, 120, 45, False),
    "privacy_choices_link": UILocation(0.50, 0.85, 220, 40, False),
    "format_selector_dropdown": UILocation(0.50, 0.30, 160, 45, False),
    "save_deck_button": UILocation(0.9635, 0.0463, 180, 50, False),
    "pagination_nav_right": UILocation(0.85, 0.85, 60, 60, False),
    "pagination_nav_left": UILocation(0.10, 0.85, 60, 60, False),
}

ASPECT_RATIO_REGISTRIES: Dict[str, Dict[str, UILocation]] = {
    "16:10": UI_LOCATIONS_16_10,
    "16:9": UI_LOCATIONS_16_9,
}


def get_location(
    name: str, screen_width: int, screen_height: int, aspect_ratio: str = "16:10"
) -> Tuple[int, int, int, int]:
    """Resolve a named UI location to absolute pixel coordinates

    for a given screen size and aspect ratio.

    Args:
        name: Key into UI locations registry.
        screen_width: Current screen width in pixels.
        screen_height: Current screen height in pixels.
        aspect_ratio: Screen aspect ratio ("16:10" or "16:9").

    Returns:
        Tuple of (x, y, width, height) in absolute pixels.

    Raises:
        KeyError: If name is not a registered UI location.
    """
    registry = ASPECT_RATIO_REGISTRIES.get(aspect_ratio, UI_LOCATIONS_16_10)
    if name not in registry:
        registry = UI_LOCATIONS_16_10
    loc = registry[name]
    if not loc.calibrated:
        logger.warning(
            "UI location '%s' for aspect ratio '%s' is UNCALIBRATED. "
            "Automation accuracy is not guaranteed at this coordinate.",
            name,
            aspect_ratio,
        )
    x = int(loc.rel_x * screen_width)
    y = int(loc.rel_y * screen_height)
    return (x, y, loc.width_px, loc.height_px)


def get_click_point(name: str, aspect_ratio: str = "16:10") -> Tuple[int, int]:
    """Resolve a named UI location to an absolute (x, y) click point.

    Uses `pyautogui.size()` to determine the current screen resolution.

    Args:
        name: Key into UI locations registry.
        aspect_ratio: Screen aspect ratio ("16:10" or "16:9").

    Returns:
        Tuple of (x, y) absolute pixel coordinates.

    Raises:
        KeyError: If name is not a registered UI location.
    """
    import pyautogui  # type: ignore[import-untyped]

    screen_width, screen_height = pyautogui.size()
    x, y, _, _ = get_location(name, screen_width, screen_height, aspect_ratio)
    return (x, y)
