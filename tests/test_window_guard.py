"""Unit tests for MTGA window focus guard."""

from unittest.mock import MagicMock, patch

import pytest

from src.automation.window_guard import ensure_mtga_focused, try_focus_mtga_window
from src.core.exceptions import AutomationError


@patch("pygetwindow.getWindowsWithTitle")
def test_try_focus_mtga_window_success(mock_get_windows: MagicMock) -> None:
    """Verify try_focus_mtga_window activates window when found."""
    mock_win = MagicMock()
    mock_win.isMinimized = False
    mock_get_windows.return_value = [mock_win]

    assert try_focus_mtga_window() is True
    mock_win.activate.assert_called_once()


@patch("pygetwindow.getWindowsWithTitle")
def test_try_focus_mtga_window_restores_minimized(mock_get_windows: MagicMock) -> None:
    """Verify try_focus_mtga_window restores window if minimized."""
    mock_win = MagicMock()
    mock_win.isMinimized = True
    mock_get_windows.return_value = [mock_win]

    assert try_focus_mtga_window() is True
    mock_win.restore.assert_called_once()
    mock_win.activate.assert_called_once()


@patch("pygetwindow.getWindowsWithTitle")
def test_try_focus_mtga_window_not_found(mock_get_windows: MagicMock) -> None:
    """Verify try_focus_mtga_window returns False when no window matches."""
    mock_get_windows.return_value = []

    assert try_focus_mtga_window() is False


@patch("src.automation.window_guard.get_focused_window_title")
def test_ensure_mtga_focused_success(mock_get_title: MagicMock) -> None:
    """Verify ensure_mtga_focused does not raise when focus succeeds."""
    mock_get_title.return_value = "Magic The Gathering: Arena"
    ensure_mtga_focused()  # Should not raise


@patch("src.automation.window_guard.get_focused_window_title")
def test_ensure_mtga_focused_raises(mock_get_title: MagicMock) -> None:
    """Verify ensure_mtga_focused raises AutomationError when focus fails."""
    mock_get_title.return_value = "Other Window"
    with pytest.raises(AutomationError):
        ensure_mtga_focused()

@patch("pygetwindow.getActiveWindow")
def test_ensure_mtga_focused_passes_when_active_window_matches(
    mock_get_active: MagicMock,
) -> None:
    """Verify ensure_mtga_focused does not raise when MTGA is the foreground window."""
    mock_win = MagicMock()
    mock_win.title = "Magic The Gathering: Arena"
    mock_get_active.return_value = mock_win

    ensure_mtga_focused()  # Should not raise


@patch("pygetwindow.getActiveWindow")
def test_ensure_mtga_focused_raises_when_active_window_does_not_match(
    mock_get_active: MagicMock,
) -> None:
    """Verify ensure_mtga_focused raises when a different window is focused."""
    mock_win = MagicMock()
    mock_win.title = "Visual Studio Code"
    mock_get_active.return_value = mock_win

    with pytest.raises(AutomationError):
        ensure_mtga_focused()


@patch("pygetwindow.getActiveWindow")
def test_ensure_mtga_focused_raises_when_no_active_window(
    mock_get_active: MagicMock,
) -> None:
    """Verify ensure_mtga_focused raises when the active window cannot be determined."""
    mock_get_active.return_value = None

    with pytest.raises(AutomationError):
        ensure_mtga_focused()
