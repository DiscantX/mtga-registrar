"""Unit tests for the emergency stop mechanism."""

import pytest

from src.automation.emergency_stop import EmergencyStop, EmergencyStopTriggered


def test_emergency_stop_trigger_and_reset() -> None:
    """Verify trigger, is_triggered, and reset behave correctly."""
    EmergencyStop.reset()
    assert EmergencyStop.is_triggered() is False

    EmergencyStop.trigger()
    assert EmergencyStop.is_triggered() is True

    EmergencyStop.reset()
    assert EmergencyStop.is_triggered() is False


def test_emergency_stop_check_raises_when_triggered() -> None:
    """Verify check() raises EmergencyStopTriggered only when the flag is set."""
    EmergencyStop.reset()
    EmergencyStop.check()  # Should not raise

    EmergencyStop.trigger()
    with pytest.raises(EmergencyStopTriggered):
        EmergencyStop.check()

    EmergencyStop.reset()
