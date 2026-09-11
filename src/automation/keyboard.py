"""Keyboard automation and typing simulation module.

This module provides human-like typing simulation, keystrokes, and hotkey combinations
for interacting with the MTGA client text fields and dialogs.
"""

import time

import pyautogui

from src.automation.timing import typing_delay
from src.core.exceptions import AutomationError


class KeyboardController:
    """Controller for human-like keyboard typing, key presses, and shortcuts."""

    @staticmethod
    def type_text(text: str, interval: float = 0.08) -> None:
        """Type a string of text character by character with randomized human-like delays.

        Args:
            text: String text to type.
            interval: Base interval between keystrokes (modified by human timing).

        Raises:
            AutomationError: If typing operation fails.
        """
        try:
            for char in text:
                pyautogui.write(char)
                delay = typing_delay()
                time.sleep(delay)
        except Exception as e:
            raise AutomationError(
                f"Failed to type text '{text[:10]}...'", details=str(e)
            ) from e

    @staticmethod
    def press_key(key: str) -> None:
        """Press and release a specific keyboard key.

        Args:
            key: Key name (e.g., 'enter', 'esc', 'backspace').

        Raises:
            AutomationError: If key press operation fails.
        """
        try:
            pyautogui.press(key)
            time.sleep(typing_delay())
        except Exception as e:
            raise AutomationError(f"Failed to press key '{key}'", details=str(e)) from e

    @staticmethod
    def hotkey(*keys: str) -> None:
        """Execute a key combination (hotkey), such as Ctrl+C or Ctrl+V.

        Args:
            *keys: Sequence of keys forming the hotkey combination.

        Raises:
            AutomationError: If hotkey execution fails.
        """
        try:
            pyautogui.hotkey(*keys)
            time.sleep(typing_delay())
        except Exception as e:
            raise AutomationError(
                f"Failed to execute hotkey combination {keys}", details=str(e)
            ) from e
