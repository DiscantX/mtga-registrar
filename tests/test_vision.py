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
    mock_pil_img = np.zeros((100, 200, 3), dtype=np.uint8)
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
    target = np.random.randint(50, 200, (200, 200, 3), dtype=np.uint8)
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
    target = np.zeros((10, 10, 3), dtype=np.uint8)
    empty_template = np.array([], dtype=np.uint8)

    with pytest.raises(VisionError):
        TemplateDetector.match_template(target, empty_template)


def test_detect_ownership_diamonds_heuristic() -> None:
    """Verify ownership diamond heuristic detection finds bright white shapes."""
    image = np.zeros((150, 150, 3), dtype=np.uint8)
    image[40:55, 40:55] = 255

    diamonds = TemplateDetector.detect_ownership_diamonds(image)
    assert len(diamonds) > 0
    assert "x" in diamonds[0]
    assert "y" in diamonds[0]
    assert "confidence" in diamonds[0]


def test_ui_detectors() -> None:
    """Verify UI element detectors return valid bounding boxes for buttons and formats."""
    canvas = np.zeros((600, 800, 3), dtype=np.uint8)

    nav_right = UIDetector.find_navigation_button(canvas, direction="right")
    assert nav_right is not None
    assert len(nav_right) == 4

    nav_left = UIDetector.find_navigation_button(canvas, direction="left")
    assert nav_left is not None

    export_btn = UIDetector.find_export_button(canvas)
    assert export_btn is not None
    assert len(export_btn) == 4

    deck_btn = UIDetector.find_deck_creation_button(canvas)
    assert deck_btn is not None

    format_btn = UIDetector.find_format_selector(canvas, format_name="Timeless")
    assert format_btn is not None
