"""Automation package for MTGA Registrar.

Provides human-like mouse movement, timing utilities, and keyboard input automation.
"""

from src.automation.keyboard import KeyboardController
from src.automation.mouse import MouseController, generate_bezier_curve
from src.automation.timing import clicking_delay, human_delay, sleep_random, typing_delay

__all__ = [
    "KeyboardController",
    "MouseController",
    "generate_bezier_curve",
    "human_delay",
    "sleep_random",
    "typing_delay",
    "clicking_delay",
]
