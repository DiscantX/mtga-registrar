"""Centralized registry of UI element locations for MTGA Registrar.

Supports aspect-ratio specific location mappings (16:10 and 16:9), screen classifications,
and JSON configuration loading/persistence exclusively from config/ui_locations.json.

All position AND size values are stored as fractions (0.0-1.0) of screen width/height,
so a single calibration works across every resolution that shares an aspect ratio.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("mtga_registrar.core.ui_locations")

CONFIG_PATH = Path("config/ui_locations.json")


class UILocation:
    """A single named UI element location, expressed entirely as fractions of screen size.

    Attributes:
        rel_x: Fraction (0.0-1.0) of screen width for the element's x position.
        rel_y: Fraction (0.0-1.0) of screen height for the element's y position.
        rel_width: Fraction (0.0-1.0) of screen width for the element's bounding
            box width (0.0 if this location is a single click point rather than a box).
        rel_height: Fraction (0.0-1.0) of screen height for the element's bounding
            box height (0.0 if this location is a single click point rather than a box).
        calibrated: True only once a human has confirmed this value against the
            real MTGA client. Must default to False for placeholder values.
        screen: Name of the screen where this UI element resides (e.g., "decks_screen").
    """

    def __init__(
        self,
        rel_x: float,
        rel_y: float,
        rel_width: float,
        rel_height: float,
        calibrated: bool,
        screen: str = "decks_screen",
    ) -> None:
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.rel_width = rel_width
        self.rel_height = rel_height
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
                rel_width = float(loc_data.get("rel_width", 0.0))
                rel_height = float(loc_data.get("rel_height", 0.0))
                calibrated = bool(loc_data.get("calibrated", False))
                screen = str(loc_data.get("screen", "decks_screen"))
                registries[ar][loc_name] = UILocation(
                    rel_x=rel_x,
                    rel_y=rel_y,
                    rel_width=rel_width,
                    rel_height=rel_height,
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
                "rel_width": loc.rel_width,
                "rel_height": loc.rel_height,
                "calibrated": loc.calibrated,
                "screen": loc.screen,
            }
        data["aspect_ratios"][ar] = ar_data  # type: ignore[index]

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("Saved UI locations to %s", CONFIG_PATH)


def update_location(
    name: str,
    aspect_ratio: str,
    rel_x: float,
    rel_y: float,
    rel_width: float,
    rel_height: float,
    calibrated: bool = True,
) -> None:
    """Update or create a UI location and save to config/ui_locations.json.

    Args:
        name: Name of the UI element.
        aspect_ratio: Aspect ratio key (e.g. "16:10" or "16:9").
        rel_x: Relative X coordinate (0.0 - 1.0).
        rel_y: Relative Y coordinate (0.0 - 1.0).
        rel_width: Relative width (0.0 - 1.0) as a fraction of screen width.
        rel_height: Relative height (0.0 - 1.0) as a fraction of screen height.
        calibrated: Calibration status flag.
    """
    if aspect_ratio not in ASPECT_RATIO_REGISTRIES:
        ASPECT_RATIO_REGISTRIES[aspect_ratio] = {}

    if name in ASPECT_RATIO_REGISTRIES[aspect_ratio]:
        loc = ASPECT_RATIO_REGISTRIES[aspect_ratio][name]
        loc.rel_x = max(0.0, min(1.0, rel_x))
        loc.rel_y = max(0.0, min(1.0, rel_y))
        loc.rel_width = max(0.0, min(1.0, rel_width))
        loc.rel_height = max(0.0, min(1.0, rel_height))
        loc.calibrated = calibrated
    else:
        ASPECT_RATIO_REGISTRIES[aspect_ratio][name] = UILocation(
            rel_x=max(0.0, min(1.0, rel_x)),
            rel_y=max(0.0, min(1.0, rel_y)),
            rel_width=max(0.0, min(1.0, rel_width)),
            rel_height=max(0.0, min(1.0, rel_height)),
            calibrated=calibrated,
            screen="decks_screen",
        )
    save_ui_locations()


# Initialize aspect ratio registries exclusively from configuration
ASPECT_RATIO_REGISTRIES: Dict[str, Dict[str, UILocation]] = load_ui_locations()

AVAILABLE_SCREENS: List[str] = [
    "decks_screen",
    "deck_editor_screen_2",
    "deck_editor_screen_3",
    "deck_editor_screen_confirmation",
    "esc_menu"
]

SCREEN_IMAGE_MAPPING: Dict[str, Dict[str, str]] = {
    "16:10": {
        "decks_screen": "screens/16-10_deck_screen.png",
        "deck_editor_screen_2": "screens/16-10_deck_editor_screen_zoom_2.png",
        "deck_editor_screen_3": "screens/16-10_deck_editor_screen_zoom_3.png",
        "deck_editor_screen_confirmation": "screens/16-10_deck_editor_screen_confirmation.png",
        "esc_menu": "screens/16-10_esc_menu.png",
    },
    "16:9": {
        "decks_screen": "screens/16-9_deck_screen.png",
        "deck_editor_screen_2": "screens/16-9_deck_editor_screen_zoom_2.png",
        "deck_editor_screen_3": "screens/16-9_deck_editor_screen_zoom_3.png",
        "deck_editor_screen_confirmation": "screens/16-9_deck_editor_screen_confirmation.png",
        "esc_menu": "screens/16-9_esc_menu.png",
    },
}


def detect_aspect_ratio(screen_width: int, screen_height: int) -> str:
    """Classify a screen resolution as '16:9' or '16:10'.

    Uses the same 1.7 threshold as `TemplateDetector.calculate_card_grid`, so
    both modules agree on which bucket a given resolution falls into.

    Args:
        screen_width: Screen width in pixels.
        screen_height: Screen height in pixels.

    Returns:
        "16:9" if width/height >= 1.7, otherwise "16:10".
    """
    if screen_height <= 0:
        return "16:10"
    ratio = screen_width / screen_height
    return "16:9" if ratio >= 1.7 else "16:10"


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
    w = int(loc.rel_width * screen_width)
    h = int(loc.rel_height * screen_height)
    return (x, y, w, h)


def get_click_point(name: str, aspect_ratio: Optional[str] = None) -> Tuple[int, int]:
    """Resolve a named UI location to an absolute (x, y) click point at its center.

    Uses `pyautogui.size()` to determine the current screen resolution. If
    `aspect_ratio` is not supplied, it is auto-detected from that resolution
    via `detect_aspect_ratio` rather than silently defaulting to "16:10" —
    this was previously a bug where every caller landed in the 16:10 bucket
    regardless of actual screen shape.

    Args:
        name: Key into UI locations registry.
        aspect_ratio: Optional explicit override ("16:10" or "16:9"). If
            None, auto-detected from the current screen resolution.

    Returns:
        Tuple of (x, y) absolute pixel coordinates at the CENTER of the
        element's bounding box (not its top-left corner).

    Raises:
        KeyError: If name is not a registered UI location.
    """
    import pyautogui  # type: ignore[import-untyped]

    screen_width, screen_height = pyautogui.size()
    resolved_ratio = aspect_ratio or detect_aspect_ratio(screen_width, screen_height)
    logger.debug(
        "get_click_point('%s'): screen=%dx%d, resolved_aspect_ratio=%s",
        name, screen_width, screen_height, resolved_ratio,
    )
    x, y, w, h = get_location(name, screen_width, screen_height, resolved_ratio)
    center_x, center_y = x + w // 2, y + h // 2
    logger.info(
        "Click target '%s' resolved to absolute point (%d, %d) "
        "[box=(%d,%d,%d,%d), screen=%dx%d, aspect_ratio=%s]",
        name, center_x, center_y, x, y, w, h, screen_width, screen_height,
        resolved_ratio,
    )
    return (center_x, center_y)
