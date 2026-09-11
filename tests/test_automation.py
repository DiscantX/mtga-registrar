"""Comprehensive unit tests for Phase 3: Input Automation & Human-Like Mechanics.

Verifies Bezier curve generation, human timing distributions, mouse control,
keyboard typing automation, and error handling.
"""

from unittest.mock import patch

import pytest

from src.automation.keyboard import KeyboardController
from src.automation.mouse import MouseController, generate_bezier_curve
from src.automation.timing import clicking_delay, human_delay, sleep_random, typing_delay
from src.core.exceptions import AutomationError


def test_timing_distributions() -> None:
    """Verify human timing delays fall within expected ranges and distributions."""
    for _ in range(50):
        d = human_delay(mean=0.1, stddev=0.03, min_delay=0.01, max_delay=0.5)
        assert 0.01 <= d <= 0.5

        td = typing_delay()
        assert 0.02 <= td <= 0.25

        cd = clicking_delay()
        assert 0.03 <= cd <= 0.4


def test_sleep_random() -> None:
    """Verify sleep_random executes successfully without errors."""
    with patch("time.sleep", return_value=None) as mock_sleep:
        sleep_random(mean=0.05, stddev=0.01)
        mock_sleep.assert_called_once()


def test_generate_bezier_curve() -> None:
    """Verify Bezier curve generation produces valid points between start and end."""
    start = (0.0, 0.0)
    end = (100.0, 100.0)
    points = generate_bezier_curve(start, end, num_points=20)

    assert len(points) == 20
    assert points[0] == start
    assert points[-1] == end

    # Check that intermediate points are not purely linear (should curve due to control offsets)
    # At least some point should deviate from linear interpolation y = x
    linear_deviations = 0
    for px, py in points[1:-1]:
        expected_y = px  # since start=(0,0) and end=(100,100)
        if abs(py - expected_y) > 0.001:
            linear_deviations += 1

    assert linear_deviations > 0


def test_mouse_controller_move() -> None:
    """Verify MouseController.move_to executes successfully with mocked pyautogui."""
    with patch("pyautogui.position", return_value=(0, 0)), \
         patch("pyautogui.moveTo") as mock_move, \
         patch("time.sleep", return_value=None):

        MouseController.move_to(50, 50, duration=0.1, steps=5)
        assert mock_move.call_count >= 5


def test_mouse_controller_click() -> None:
    """Verify MouseController.click executes click action correctly."""
    with patch("pyautogui.click") as mock_click, \
         patch("pyautogui.position", return_value=(0, 0)), \
         patch("pyautogui.moveTo"), \
         patch("time.sleep", return_value=None):

        MouseController.click(10, 20, button="left")
        mock_click.assert_called_once_with(button="left")


def test_mouse_controller_drag() -> None:
    """Verify MouseController.drag executes mouse drag action correctly."""
    with patch("pyautogui.mouseDown") as mock_down, \
         patch("pyautogui.mouseUp") as mock_up, \
         patch("pyautogui.position", return_value=(0, 0)), \
         patch("pyautogui.moveTo"), \
         patch("time.sleep", return_value=None):

        MouseController.drag(0, 0, 100, 100, duration=0.1)
        mock_down.assert_called_once()
        mock_up.assert_called_once()


def test_mouse_controller_error() -> None:
    """Verify MouseController raises AutomationError on failure."""
    with patch("pyautogui.position", side_effect=Exception("Lost cursor")):
        with pytest.raises(AutomationError) as exc_info:
            MouseController.move_to(10, 10)
        assert "Failed to move mouse" in str(exc_info.value)


def test_keyboard_controller_type() -> None:
    """Verify KeyboardController.type_text types characters and sleeps."""
    with patch("pyautogui.write") as mock_write, \
         patch("time.sleep", return_value=None):

        KeyboardController.type_text("test")
        assert mock_write.call_count == 4


def test_keyboard_controller_press() -> None:
    """Verify KeyboardController.press_key presses key correctly."""
    with patch("pyautogui.press") as mock_press, \
         patch("time.sleep", return_value=None):

        KeyboardController.press_key("enter")
        mock_press.assert_called_once_with("enter")


def test_keyboard_controller_hotkey() -> None:
    """Verify KeyboardController.hotkey executes key combinations."""
    with patch("pyautogui.hotkey") as mock_hotkey, \
         patch("time.sleep", return_value=None):

        KeyboardController.hotkey("ctrl", "c")
        mock_hotkey.assert_called_once_with("ctrl", "c")


def test_keyboard_controller_error() -> None:
    """Verify KeyboardController raises AutomationError on failure."""
    with patch("pyautogui.write", side_effect=Exception("Keyboard disconnected")):
        with pytest.raises(AutomationError) as exc_info:
            KeyboardController.type_text("abc")
        assert "Failed to type text" in str(exc_info.value)
