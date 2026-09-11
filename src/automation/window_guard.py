"""MTGA Window Focus Guard for MTGA Registrar.

Provides utilities to detect, focus, and verify the Magic: The Gathering Arena window
before automation begins.
"""

import logging

from src.core.exceptions import AutomationError

logger = logging.getLogger("mtga_registrar.automation.window_guard")
window_title_substring = "Magic The Gathering: Arena"


def try_focus_mtga_window(title_hint: str = window_title_substring) -> bool:
    """Attempt to find and focus the MTGA window.

    Args:
        title_hint: Substring or title to match window against.

    Returns:
        True if window was found and activated successfully, False otherwise.
    """
    try:
        import pygetwindow as gw  # type: ignore[import-untyped]

        windows = gw.getWindowsWithTitle(title_hint)
        if not windows:
            for alt in ["MTGA", "Magic"]:
                windows = gw.getWindowsWithTitle(alt)
                if windows:
                    break

        if windows:
            win = windows[0]
            if getattr(win, "isMinimized", False):
                win.restore()
            win.activate()
            logger.info("Successfully focused MTGA window: %s", getattr(win, "title", title_hint))
            return True
        else:
            logger.warning("No window matching title hint '%s' found.", title_hint)
            return False
    except Exception as e:
        logger.warning("Failed to focus MTGA window via pygetwindow: %s", e)
        return False


def ensure_mtga_focused(title_hint: str = window_title_substring) -> None:
    """Ensure the MTGA window is focused, raising AutomationError if focus fails.

    Args:
        title_hint: Substring or title to match window against.

    Raises:
        AutomationError: If the MTGA window cannot be found or focused.
    """
    if not try_focus_mtga_window(title_hint):
        raise AutomationError(
            f"Could not find or focus MTGA window (title hint: '{title_hint}'). "
            "Please ensure MTGA is running and visible."
        )
