"""Variable delay and natural timing utilities for human-like automation.

This module provides Gaussian and randomized delay distributions for typing,
clicking, and mouse movements to prevent bot detection in MTGA Registrar.
"""

import random
import time


def human_delay(
    mean: float = 0.1,
    stddev: float = 0.03,
    min_delay: float = 0.01,
    max_delay: float = 0.5,
) -> float:
    """Generate a randomized human-like delay using a Gaussian normal distribution.

    Args:
        mean: Mean delay duration in seconds.
        stddev: Standard deviation of the delay duration in seconds.
        min_delay: Absolute minimum delay floor in seconds.
        max_delay: Absolute maximum delay ceiling in seconds.

    Returns:
        float: Randomized delay duration in seconds.
    """
    delay = random.gauss(mean, stddev)
    return max(min_delay, min(delay, max_delay))


def sleep_random(
    mean: float = 0.1,
    stddev: float = 0.03,
    min_delay: float = 0.01,
    max_delay: float = 0.5,
) -> None:
    """Sleep for a randomized human-like duration.

    Args:
        mean: Mean delay duration in seconds.
        stddev: Standard deviation of the delay duration in seconds.
        min_delay: Absolute minimum delay floor in seconds.
        max_delay: Absolute maximum delay ceiling in seconds.
    """
    delay = human_delay(mean=mean, stddev=stddev, min_delay=min_delay, max_delay=max_delay)
    time.sleep(delay)


def typing_delay() -> float:
    """Generate a natural keystroke typing delay.

    Returns:
        float: Delay duration in seconds suitable between key presses.
    """
    return human_delay(mean=0.07, stddev=0.02, min_delay=0.02, max_delay=0.25)


def clicking_delay() -> float:
    """Generate a natural pre/post click pause duration.

    Returns:
        float: Delay duration in seconds around mouse clicks.
    """
    return human_delay(mean=0.12, stddev=0.04, min_delay=0.03, max_delay=0.4)
