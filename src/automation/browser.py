"""Browser automation and navigation module for GeForce Now.

This module provides `BrowserController` to automate browser navigation (such as navigating
the GeForce Now in-game Edge browser to the temporary Tunnelmole public URL) using human-like
keyboard shortcuts, typing delays, and mouse interactions.
"""

import logging
from typing import Optional

from src.automation.keyboard import KeyboardController
from src.automation.mouse import MouseController
from src.automation.timing import sleep_random
from src.core.exceptions import AutomationError
from src.core.ui_locations import get_click_point

logger = logging.getLogger("mtga_registrar")


class BrowserController:
    """Controller for browser navigation and interaction within GeForce Now."""

    @staticmethod
    def navigate_to_url(url: str, address_bar_coords: Optional[tuple[int, int]] = None) -> None:
        """Navigate the browser to the specified URL (e.g., https://*.tunnelmole.net).

        Uses keyboard shortcuts (Ctrl+L or Alt+D) to focus the address bar, types the URL
        with human-like typing delays, and presses Enter. Optionally clicks specific address
        bar coordinates if provided.

        Args:
            url: The destination URL string (e.g., Tunnelmole forwarding URL).
            address_bar_coords: Optional (x, y) coordinates to click the address bar directly.

        Raises:
            AutomationError: If browser navigation fails.
        """
        try:
            logger.info("[SEQ:navigate] Ctrl+L -> type tunnel URL -> Enter.")
            if not isinstance(url, str) or not url.startswith("http"):
                raise AutomationError(f"Invalid URL provided for navigation: '{url}'")

            logger.info(f"Navigating browser to URL: {url}")

            # Optional click on address bar coordinates if provided
            if address_bar_coords is not None:
                x, y = address_bar_coords
                MouseController.click(x, y)
                sleep_random(0.1, 0.03, 0.05, 0.2)
            else:
                # Use standard browser address bar focus hotkeys (Ctrl+L or Alt+D)
                KeyboardController.hotkey("ctrl", "l")
                sleep_random(0.15, 0.03, 0.08, 0.25)

            # Clear existing text in address bar just in case
            KeyboardController.hotkey("ctrl", "a")
            sleep_random(0.05, 0.01, 0.02, 0.1)

            # Type the URL with human-like delays
            KeyboardController.type_text(url, interval=0.04)
            sleep_random(0.1, 0.03, 0.05, 0.2)

            # Press Enter to navigate
            KeyboardController.press_key("enter")

            # Allow time for page load / navigation initiation
            sleep_random(1.0, 0.2, 0.5, 2.0)
            logger.debug(f"Successfully triggered browser navigation to {url}")

        except Exception as e:
            logger.error(f"Failed to navigate browser to URL '{url}': {e}")
            if isinstance(e, AutomationError):
                raise
            raise AutomationError(
                f"Browser navigation failed for URL '{url}'", details=str(e)
            ) from e

    @staticmethod
    def open_help_link_or_browser(click_coords: Optional[tuple[int, int]] = None) -> None:
        """Open the in-game Edge browser or help link in GeForce Now.

        Args:
            click_coords: Optional (x, y) coordinates of the help/link icon in MTGA or GFN overlay.

        Raises:
            AutomationError: If opening browser/link fails.
        """
        try:
            if click_coords is not None:
                x, y = click_coords
                MouseController.click(x, y)
            else:
                # Fallback hotkeys or shortcut (e.g. Win+D or browser shortcut)
                KeyboardController.hotkey("ctrl", "shift", "o")

            sleep_random(0.5, 0.1, 0.3, 1.0)
            logger.debug("Successfully triggered open help/browser action.")
        except Exception as e:
            logger.error(f"Failed to open browser or help link: {e}")
            if isinstance(e, AutomationError):
                raise
            raise AutomationError("Failed to open browser or help link", details=str(e)) from e

    @staticmethod
    def open_privacy_browser(click_coords: Optional[tuple[int, int]] = None) -> None:
        """Press ESC to open menu, then click 'Your Privacy Choices' to launch browser.

        Args:
            click_coords: Optional (x, y) coordinates of the 'Your Privacy Choices' link.

        Raises:
            AutomationError: If opening privacy browser fails.
        """
        try:
            logger.info("[SEQ:privacy_browser] ESC -> click 'Your Privacy Choices' to open Edge.")
            logger.info("Opening privacy browser via ESC menu...")
            KeyboardController.press_key("esc")
            sleep_random(0.3, 0.05, 0.1, 0.5)

            if click_coords is not None:
                x, y = click_coords
                MouseController.click(x, y)
            else:
                MouseController.click(*get_click_point("privacy_choices_link"))

            sleep_random(1.0, 0.2, 0.5, 2.0)
            logger.debug("Successfully opened privacy browser.")
        except Exception as e:
            logger.error(f"Failed to open privacy browser: {e}")
            if isinstance(e, AutomationError):
                raise
            raise AutomationError("Failed to open privacy browser", details=str(e)) from e

    @staticmethod
    def navigate_and_transfer(
        url: str,
        address_bar_coords: Optional[tuple[int, int]] = None,
    ) -> None:
        """Navigate address bar to Tunnelmole URL and transmit clipboard payload.

        Args:
            url: Tunnelmole forwarding URL.
            address_bar_coords: Optional (x, y) coordinates for address bar.

        Raises:
            AutomationError: If navigation fails.
        """
        BrowserController.navigate_to_url(url, address_bar_coords=address_bar_coords)

    @staticmethod
    def close_current_tab() -> None:
        """Send Ctrl+W to close the Edge tab and free Tunnelmole single-connection limit.

        Raises:
            AutomationError: If closing tab fails.
        """
        try:
            logger.info("[SEQ:close_tab] Ctrl+W to close browser tab.")
            logger.info("Closing current browser tab via Ctrl+W...")
            KeyboardController.hotkey("ctrl", "w")
            sleep_random(0.5, 0.1, 0.2, 0.8)
            logger.debug("Successfully closed browser tab.")
        except Exception as e:
            logger.error(f"Failed to close current browser tab: {e}")
            if isinstance(e, AutomationError):
                raise
            raise AutomationError("Failed to close current browser tab", details=str(e)) from e
