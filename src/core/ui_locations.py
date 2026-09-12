"""Centralized registry of UI element locations for MTGA Registrar.

Supports aspect-ratio specific location mappings (16:10 and 16:9), screen classifications,
and JSON configuration loading/persistence with fallback defaults.
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


# Built-in Default 16:10 Aspect Ratio UI Registry (Calibrated from 16:10 screenshots)
_BUILTIN_UI_LOCATIONS_16_10: Dict[str, UILocation] = {
    "create_deck_button": UILocation(0.108, 0.421, 307, 260, True, "decks_screen"),
    "decks_search_bar": UILocation(0.233, 0.125, 460, 40, True, "decks_screen"),
    "leftmost_deck_slot": UILocation(0.278, 0.421, 307, 260, True, "decks_screen"),
    "export_deck_button": UILocation(0.330, 0.930, 40, 40, True, "decks_screen"),
    "trash_can_button": UILocation(0.435, 0.930, 40, 40, True, "decks_screen"),
    "confirmation_ok_button": UILocation(0.547, 0.602, 120, 45, True, "decks_screen"),
    "privacy_choices_link": UILocation(0.500, 0.833, 220, 40, True, "esc_screen"),
    "format_selector_dropdown": UILocation(0.900, 0.127, 200, 45, True, "deck_editor_screen"),
    "save_deck_button": UILocation(0.892, 0.930, 180, 50, True, "deck_editor_screen"),
    "pagination_nav_right": UILocation(0.742, 0.588, 40, 60, True, "deck_editor_screen"),
    "pagination_nav_left": UILocation(0.042, 0.680, 40, 60, True, "deck_editor_screen"),
}

# Built-in Default 16:9 Aspect Ratio UI Registry (Placeholder / Uncalibrated)
_BUILTIN_UI_LOCATIONS_16_9: Dict[str, UILocation] = {
    "create_deck_button": UILocation(0.15, 0.15, 140, 50, False, "decks_screen"),
    "decks_search_bar": UILocation(0.70, 0.12, 200, 40, False, "decks_screen"),
    "leftmost_deck_slot": UILocation(0.15, 0.30, 180, 220, False, "decks_screen"),
    "export_deck_button": UILocation(0.25, 0.90, 120, 40, False, "decks_screen"),
    "trash_can_button": UILocation(0.85, 0.15, 50, 50, False, "decks_screen"),
    "confirmation_ok_button": UILocation(0.55, 0.60, 120, 45, False, "decks_screen"),
    "privacy_choices_link": UILocation(0.50, 0.85, 220, 40, False, "esc_screen"),
    "format_selector_dropdown": UILocation(0.50, 0.30, 160, 45, False, "deck_editor_screen"),
    "save_deck_button": UILocation(0.9635, 0.0463, 180, 50, False, "deck_editor_screen"),
    "pagination_nav_right": UILocation(0.85, 0.85, 60, 60, False, "deck_editor_screen"),
    "pagination_nav_left": UILocation(0.10, 0.85, 60, 60, False, "deck_editor_screen"),
}


def load_ui_locations() -> Dict[str, Dict[str, UILocation]]:
    """Load UI locations from config/ui_locations.json, falling back to built-in defaults.

    Returns:
        Dictionary mapping aspect ratios to dictionaries of UILocation instances.
    """
    registries: Dict[str, Dict[str, UILocation]] = {
        "16:10": dict(_BUILTIN_UI_LOCATIONS_16_10),
        "16:9": dict(_BUILTIN_UI_LOCATIONS_16_9),
    }

    if not CONFIG_PATH.exists():
        logger.info(
            "UI locations config %s not found. Using and saving default locations.",
            CONFIG_PATH,
        )
        try:
            save_ui_locations(registries)
        except Exception as e:
            logger.warning(
                "Failed to write default UI locations config to %s: %s",
                CONFIG_PATH,
                e,
            )
        return registries

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

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
                        "Error parsing UI location '%s' for aspect ratio '%s': %s. "
                        "Using default if available.",
                        loc_name,
                        ar,
                        entry_err,
                    )
        logger.info("Successfully loaded UI locations from %s", CONFIG_PATH)
    except Exception as e:
        logger.error(
            "Failed to load UI locations from %s: %s. Falling back to built-in defaults.",
            CONFIG_PATH,
            e,
        )

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


# Initialize aspect ratio registries from configuration (with fallback defaults)
ASPECT_RATIO_REGISTRIES: Dict[str, Dict[str, UILocation]] = load_ui_locations()

UI_LOCATIONS_16_10: Dict[str, UILocation] = ASPECT_RATIO_REGISTRIES.get(
    "16:10", _BUILTIN_UI_LOCATIONS_16_10
)
UI_LOCATIONS_16_9: Dict[str, UILocation] = ASPECT_RATIO_REGISTRIES.get(
    "16:9", _BUILTIN_UI_LOCATIONS_16_9
)

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
