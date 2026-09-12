"""Centralized registry of UI element locations for MTGA Registrar.

Supports aspect-ratio specific location mappings (16:10 and 16:9), screen classifications,
and JSON configuration loading/persistence exclusively from config/ui_locations.json.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("mtga_registrar.core.ui_locations")

CONFIG_PATH = Path("config/ui_locations.json")


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
        screen: Name of the screen where this UI element resides (e.g., "decks_screen").
    """

    def __init__(
        self,
        rel_x: float,
        rel_y: float,
        width_px: int,
        height_px: int,
        calibrated: bool,
        screen: str = "decks_screen",
    ) -> None:
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.width_px = width_px
        self.height_px = height_px
        self.calibrated = calibrated
        self.screen = screen


def load_ui_locations() -> Dict[str, Dict[str, UILocation]]:
    """Load UI locations exclusively from config/ui_locations.json.

    Returns:
        Dictionary mapping aspect ratios to dictionaries of UILocation instances.

    Raises:
        FileNotFoundError: If config/ui_locations.json does not exist.
        json.JSONDecodeError: If config/ui_locations.json is invalid JSON.
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"UI locations config {CONFIG_PATH} not found. "
            "config/ui_locations.json is the sole source of truth."
        )

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    registries: Dict[str, Dict[str, UILocation]] = {}
    aspect_ratios_data = data.get("aspect_ratios", {})
    for ar, ar_dict in aspect_ratios_data.items():
        if ar not in registries:
            registries[ar] = {}
        for loc_name, loc_data in ar_dict.items():
            try:
                rel_x = float(loc_data.get("rel_x", 0.0))
                rel_y = float(loc_data.get("rel_y", 0.0))
                width_px = int(loc_data.get("width_px", 0))
                height_px = int(loc_data.get("height_px", 0))
                calibrated = bool(loc_data.get("calibrated", False))
                screen = str(loc_data.get("screen", "decks_screen"))
                registries[ar][loc_name] = UILocation(
                    rel_x=rel_x,
                    rel_y=rel_y,
                    width_px=width_px,
                    height_px=height_px,
                    calibrated=calibrated,
                    screen=screen,
                )
            except Exception as entry_err:
                logger.warning(
                    "Error parsing UI location '%s' for aspect ratio '%s': %s.",
                    loc_name,
                    ar,
                    entry_err,
                )
    logger.info("Successfully loaded UI locations from %s", CONFIG_PATH)
    return registries


def save_ui_locations(
    registries: Optional[Dict[str, Dict[str, UILocation]]] = None,
) -> None:
    """Save UI locations registries to config/ui_locations.json.

    Args:
        registries: Optional mapping of aspect ratios to UILocation dictionaries.
            If None, uses global ASPECT_RATIO_REGISTRIES.
    """
    if registries is None:
        registries = ASPECT_RATIO_REGISTRIES

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "version": "1.0",
        "aspect_ratios": {}
    }

    for ar, ar_dict in registries.items():
        ar_data = {}
        for loc_name, loc in ar_dict.items():
            ar_data[loc_name] = {
                "rel_x": loc.rel_x,
                "rel_y": loc.rel_y,
                "width_px": loc.width_px,
                "height_px": loc.height_px,
                "calibrated": loc.calibrated,
                "screen": loc.screen,
            }
        data["aspect_ratios"][ar] = ar_data  # type: ignore[index]

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("Saved UI locations to %s", CONFIG_PATH)


# Initialize aspect ratio registries exclusively from configuration
ASPECT_RATIO_REGISTRIES: Dict[str, Dict[str, UILocation]] = load_ui_locations()

AVAILABLE_SCREENS: List[str] = [
    "decks_screen",
    "deck_editor_screen",
]

SCREEN_IMAGE_MAPPING: Dict[str, Dict[str, str]] = {
    "16:10": {
        "decks_screen": "screens/16-10_deck_screen.png",
        "deck_editor_screen": "screens/16-10_deck_editor_screen_zoom_2.png",
    },
    "16:9": {
        "decks_screen": "screens/16-10_deck_screen.png",
        "deck_editor_screen": "screens/16-10_deck_editor_screen_zoom_2.png",
    },
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
    registry = ASPECT_RATIO_REGISTRIES.get(aspect_ratio)
    if not registry:
        registry = ASPECT_RATIO_REGISTRIES.get("16:10", {})
    if name not in registry:
        registry = ASPECT_RATIO_REGISTRIES.get("16:10", {})
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
