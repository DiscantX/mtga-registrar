"""Tests for UI locations registry, aspect ratio detection, and click point resolution."""

from src.core.ui_locations import (
    detect_aspect_ratio,
    get_click_point,
    get_location,
    load_ui_locations,
)


def test_detect_aspect_ratio() -> None:
    """Verify aspect ratio classification based on screen width/height."""
    assert detect_aspect_ratio(1920, 1080) == "16:9"
    assert detect_aspect_ratio(2560, 1600) == "16:10"
    assert detect_aspect_ratio(1280, 800) == "16:10"
    assert detect_aspect_ratio(1920, 1200) == "16:10"
    assert detect_aspect_ratio(0, 0) == "16:10"


def test_load_ui_locations() -> None:
    """Verify loading UI locations returns valid registries."""
    registries = load_ui_locations()
    assert "16:9" in registries
    assert "16:10" in registries
    assert "create_deck_button" in registries["16:9"]
    assert "create_deck_button" in registries["16:10"]


def test_get_location() -> None:
    """Verify getting absolute location coordinates."""
    x, y, w, h = get_location("create_deck_button", 1920, 1080, "16:9")
    assert isinstance(x, int)
    assert isinstance(y, int)
    assert isinstance(w, int)
    assert isinstance(h, int)
    assert w > 0
    assert h > 0


def test_get_click_point() -> None:
    """Verify getting click center points."""
    cx, cy = get_click_point("create_deck_button", aspect_ratio="16:9")
    assert isinstance(cx, int)
    assert isinstance(cy, int)
