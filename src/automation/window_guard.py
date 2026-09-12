"""MTGA Window Focus Guard for MTGA Registrar.

Provides utilities to detect, focus, and verify the Magic: The Gathering Arena window
before automation begins.
"""

import logging
from typing import Optional

from src.core.exceptions import AutomationError

logger = logging.getLogger("mtga_registrar.automation.window_guard")
window_title_substring = "Magic the Gathering: Arena"


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

def get_focused_window_title() -> Optional[str]:
    """Get the title of the currently focused (active) window.

    Returns:
        The active window's title string, or None if it cannot be determined.
    """
    try:
        import pygetwindow as gw  # type: ignore[import-untyped]

        active = gw.getActiveWindow()
        return active.title if active is not None else None
    except Exception as e:
        logger.warning("Failed to read the focused window title: %s", e)
        return None

def ensure_mtga_focused(title_hint: str = window_title_substring) -> None:
    """Verify the MTGA window is the currently focused (foreground) window.

    This does NOT attempt to focus the window itself — call
    `try_focus_mtga_window()` first if that's needed. This function only
    checks whether focus actually landed on MTGA afterward.

    Args:
        title_hint: Substring or title to match window against.

    Raises:
        AutomationError: If the currently focused window's title does not
            contain `title_hint`.
    """
    title = get_focused_window_title()
    if title is None or title_hint.lower() not in title.lower():
        raise AutomationError(
            "MTGA Arena window is not focused; refusing to run automation.",
            details=f"Focused window title: {title!r}",
        )
    logger.info("Confirmed MTGA window is focused: '%s'", title)
