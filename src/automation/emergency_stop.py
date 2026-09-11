"""Emergency stop mechanism for MTGA Registrar.

Provides a global, thread-safe flag that a hotkey listener can set to signal all
automation loops to halt immediately.
"""

import logging
import threading

from src.core.exceptions import AutomationError

logger = logging.getLogger("mtga_registrar.automation.emergency_stop")


class EmergencyStopTriggered(AutomationError):  # noqa: N818
    """Raised when automation detects the emergency stop flag has been set."""

    pass


class EmergencyStop:
    """Thread-safe global stop signal for aborting automation mid-run."""

    _event = threading.Event()

    @classmethod
    def is_triggered(cls) -> bool:
        """Check whether an emergency stop has been triggered.

        Returns:
            True if the emergency stop flag is currently set.
        """
        return cls._event.is_set()

    @classmethod
    def trigger(cls) -> None:
        """Set the emergency stop flag."""
        logger.warning("EMERGENCY STOP triggered! Automation will halt at the next checkpoint.")
        cls._event.set()

    @classmethod
    def reset(cls) -> None:
        """Clear the emergency stop flag, e.g. before starting a new run."""
        cls._event.clear()

    @classmethod
    def check(cls) -> None:
        """Raise EmergencyStopTriggered if the stop flag is currently set.

        Raises:
            EmergencyStopTriggered: If the emergency stop flag is set.
        """
        if cls.is_triggered():
            raise EmergencyStopTriggered("Emergency stop was triggered by the user.")

    @classmethod
    def start_hotkey_listener(cls, hotkey: str = "ctrl+alt+q") -> None:
        """Start a background listener that triggers the emergency stop on hotkey press.

        Args:
            hotkey: Key combination string (default: 'ctrl+alt+q').
        """
        try:
            import keyboard  # type: ignore[import-untyped]

            keyboard.add_hotkey(hotkey, cls.trigger)
            logger.info("Emergency stop hotkey registered: %s", hotkey)
        except Exception as e:
            logger.error("Failed to register emergency stop hotkey: %s", e)
