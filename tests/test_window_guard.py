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


@patch("src.automation.window_guard.try_focus_mtga_window")
def test_ensure_mtga_focused_success(mock_try_focus: MagicMock) -> None:
    """Verify ensure_mtga_focused does not raise when focus succeeds."""
    mock_try_focus.return_value = True
    ensure_mtga_focused()  # Should not raise


@patch("src.automation.window_guard.try_focus_mtga_window")
def test_ensure_mtga_focused_raises(mock_try_focus: MagicMock) -> None:
    """Verify ensure_mtga_focused raises AutomationError when focus fails."""
    mock_try_focus.return_value = False
    with pytest.raises(AutomationError):
        ensure_mtga_focused()
