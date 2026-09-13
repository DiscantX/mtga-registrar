"""Comprehensive unit tests for Phase 2: Vision & UI Perception Module.

Verifies screen capture, template matching, ownership diamond detection,
and UI element detectors using synthetic mock images and mock patchers.
"""

from unittest.mock import patch

import numpy as np
import pytest

from src.core.exceptions import VisionError
from src.vision.capture import ScreenCapture
from src.vision.detector import TemplateDetector
from src.vision.ui import UIDetector


def test_screen_capture_success() -> None:
    """Verify screen capture successfully returns a BGR numpy array when mocked."""
    mock_pil_img: np.ndarray = np.zeros((100, 200, 3), dtype=np.uint8)
    from PIL import Image
    img = Image.fromarray(mock_pil_img, mode="RGB")

    with patch("pyautogui.screenshot", return_value=img):
        result = ScreenCapture.capture_screen(region=(0, 0, 200, 100))
        assert isinstance(result, np.ndarray)
        assert result.shape == (100, 200, 3)


def test_screen_capture_failure() -> None:
    """Verify screen capture raises VisionError when pyautogui throws an exception."""
    with patch("pyautogui.screenshot", side_effect=Exception("Display disconnected")):
        with pytest.raises(VisionError) as exc_info:
            ScreenCapture.capture_screen()
        assert "Screen capture failed" in str(exc_info.value)


def test_template_matching_success() -> None:
    """Verify template matching locates a template within a target image correctly."""
    np.random.seed(42)
    target: np.ndarray = np.random.randint(50, 200, (200, 200, 3), dtype=np.uint8)
    pattern = np.array([[[255, 0, 255], [0, 255, 0]], [[255, 255, 0], [0, 0, 255]]], dtype=np.uint8)
    import cv2
    pattern_resized = cv2.resize(pattern, (20, 20), interpolation=cv2.INTER_NEAREST)
    target[60:80, 50:70] = pattern_resized

    template = pattern_resized.copy()

    matches = TemplateDetector.match_template(target, template, threshold=0.9)
    assert len(matches) > 0
    x, y, w, h, conf = matches[0]
    assert x == 50
    assert y == 60
    assert w == 20
    assert h == 20
    assert conf >= 0.9


def test_template_matching_invalid_input() -> None:
    """Verify match_template raises VisionError on invalid inputs."""
    target: np.ndarray = np.zeros((10, 10, 3), dtype=np.uint8)
    empty_template = np.array([], dtype=np.uint8)

    with pytest.raises(VisionError):
        TemplateDetector.match_template(target, empty_template)


def test_detect_ownership_diamonds_heuristic() -> None:
    """Verify ownership diamond heuristic detection finds bright white shapes."""
    image: np.ndarray = np.zeros((150, 150, 3), dtype=np.uint8)
    image[40:55, 40:55] = 255

    diamonds = TemplateDetector.detect_ownership_diamonds(image)
    assert len(diamonds) > 0
    assert "x" in diamonds[0]
    assert "y" in diamonds[0]
    assert "confidence" in diamonds[0]


def test_ui_detectors() -> None:
    """Verify UI element detectors return valid bounding boxes for buttons and formats."""
    canvas: np.ndarray = np.zeros((600, 800, 3), dtype=np.uint8)

    export_btn = UIDetector.find_export_button(canvas)
    assert export_btn is not None
    assert len(export_btn) == 4

    deck_btn = UIDetector.find_deck_creation_button(canvas)
    assert deck_btn is not None

    format_btn = UIDetector.find_format_selector(canvas, format_name="Timeless")
    assert format_btn is not None


def test_calculate_card_grid_16_9() -> None:
    """Verify card grid calculation for 16:9 aspect ratio (1920x1080) at zoom levels 2 and 3."""
    # 1920x1080 -> 16:9
    image_shape = (1080, 1920, 3)

    # Zoom level 2 (standard): 2 rows x 5 columns = 10 slots
    grid_zoom2 = TemplateDetector.calculate_card_grid(image_shape, zoom_level=2)
    assert len(grid_zoom2) == 10
    assert len(grid_zoom2[0]) == 4  # (x, y, w, h)

    # Zoom level 3 (zoomed out): 3 rows x 7 columns = 21 slots
    grid_zoom3 = TemplateDetector.calculate_card_grid(image_shape, zoom_level=3)
    assert len(grid_zoom3) == 21


def test_calculate_card_grid_16_10() -> None:
    """Verify card grid calculation for 16:10 aspect ratio (1920x1200) at zoom levels 2 and 3."""
    # 1920x1200 -> 16:10 (ar = 1.6)
    image_shape = (1200, 1920, 3)

    # Zoom level 2 (standard): 2 rows x 4 columns = 8 slots
    grid_zoom2 = TemplateDetector.calculate_card_grid(image_shape, zoom_level=2)
    assert len(grid_zoom2) == 8

    # Zoom level 3 (zoomed out): 3 rows x 6 columns = 18 slots
    grid_zoom3 = TemplateDetector.calculate_card_grid(image_shape, zoom_level=3)
    assert len(grid_zoom3) == 18


def test_calculate_card_grid_16_10_calibrated_values() -> None:
    """Verify zoom-level-2 slot coordinates match calibrated JSON values exactly."""
    image_shape = (1200, 1920, 3)  # 16:10
    grid = TemplateDetector.calculate_card_grid(image_shape, zoom_level=2)
    expected = [
        (528, 241, 300, 418),
        (878, 241, 300, 418),
        (1228, 241, 300, 418),
        (1578, 241, 300, 418),
        (528, 768, 300, 418),
        (878, 768, 300, 418),
        (1228, 768, 300, 418),
        (1578, 768, 300, 418),
    ]
    assert grid == expected


def test_calculate_card_grid_16_9_calibrated_values() -> None:
    """Verify zoom-level-2 slot coordinates match calibrated JSON values exactly."""
    image_shape = (1080, 1920, 3)  # 16:9
    grid = TemplateDetector.calculate_card_grid(image_shape, zoom_level=2)
    expected = [
        (43, 194, 259, 364),
        (328, 194, 259, 364),
        (613, 194, 259, 364),
        (898, 194, 259, 364),
        (1183, 194, 259, 364),
        (43, 662, 259, 364),
        (328, 662, 259, 364),
        (613, 662, 259, 364),
        (898, 662, 259, 364),
        (1183, 662, 259, 364),
    ]
    assert grid == expected


def test_calculate_card_grid_invalid_shape() -> None:
    """Verify calculate_card_grid raises VisionError on invalid or empty image shapes."""
    with pytest.raises(VisionError):
        TemplateDetector.calculate_card_grid((0, 0))


def test_evaluate_card_ownership_quantities() -> None:
    """Verify evaluate_card_ownership correctly counts 0 to 4 bright diamond indicators."""
    # Create mock card slot image (e.g. 200x150)
    slot_img: np.ndarray = np.zeros((150, 200, 3), dtype=np.uint8)

    # Header region is roughly y: 2% to 28% (3 to 42), x: 10% to 90% (20 to 180)
    # 4 segments across x: 20 to 180 -> width 160 -> 40 pixels per segment

    # Test 0 diamonds
    assert TemplateDetector.evaluate_card_ownership(slot_img) == 0

    # Test 1 diamond (first segment)
    img_1 = slot_img.copy()
    img_1[10:30, 30:50] = 255
    assert TemplateDetector.evaluate_card_ownership(img_1) == 1

    # Test 2 diamonds (first two segments)
    img_2 = slot_img.copy()
    img_2[10:30, 30:50] = 255
    img_2[10:30, 70:90] = 255
    assert TemplateDetector.evaluate_card_ownership(img_2) == 2

    # Test 3 diamonds
    img_3 = slot_img.copy()
    img_3[10:30, 30:50] = 255
    img_3[10:30, 70:90] = 255
    img_3[10:30, 110:130] = 255
    assert TemplateDetector.evaluate_card_ownership(img_3) == 3

    # Test 4 diamonds
    img_4 = slot_img.copy()
    img_4[10:30, 30:50] = 255
    img_4[10:30, 70:90] = 255
    img_4[10:30, 110:130] = 255
    img_4[10:30, 150:170] = 255
    assert TemplateDetector.evaluate_card_ownership(img_4) == 4


def test_evaluate_card_ownership_infinity() -> None:
    """Verify evaluate_card_ownership detects infinity symbol and returns 1."""
    slot_img: np.ndarray = np.zeros((150, 200, 3), dtype=np.uint8)
    # Draw an infinity-like symbol region in the header
    slot_img[10:25, 60:100] = 255
    assert TemplateDetector.evaluate_card_ownership(slot_img) == 1


def test_evaluate_card_ownership_invalid() -> None:
    """Verify evaluate_card_ownership raises VisionError on invalid image input."""
    with pytest.raises(VisionError):
        TemplateDetector.evaluate_card_ownership(np.array([], dtype=np.uint8))


