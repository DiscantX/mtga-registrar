"""Bezier curve mouse movement and human-like interaction module.

This module provides non-linear mouse path generation and movement controllers
to simulate natural hand movements when interacting with the MTGA client.
"""

import logging
import math
import random
import time
from typing import Optional, Tuple

import pyautogui

from src.automation.timing import sleep_random
from src.core.exceptions import AutomationError

logger = logging.getLogger("mtga_registrar.automation.mouse")

# Ensure PyAutoGUI failsafe is enabled or configured safely
pyautogui.FAILSAFE = True


def generate_bezier_curve(
    start: Tuple[float, float],
    end: Tuple[float, float],
    num_points: int = 50,
    control_offset_range: Tuple[float, float] = (-60.0, 60.0),
) -> list[Tuple[float, float]]:
    """Generate a smooth non-linear Bezier curve trajectory between start and end points.

    Args:
        start: Starting (x, y) coordinates.
        end: Ending (x, y) coordinates.
        num_points: Number of discrete points along the curve.
        control_offset_range: Min and max offset range for control points.

    Returns:
        list[Tuple[float, float]]: List of (x, y) coordinate tuples along the path.
    """
    x1, y1 = start
    x2, y2 = end

    distance = math.hypot(x2 - x1, y2 - y1)
    if distance < 5.0 or num_points < 2:
        return [start, end]

    # Generate random control points for cubic Bezier curve
    offset_min, offset_max = control_offset_range
    cx1 = x1 + (x2 - x1) * 0.33 + random.uniform(offset_min, offset_max)
    cy1 = y1 + (y2 - y1) * 0.33 + random.uniform(offset_min, offset_max)
    cx2 = x1 + (x2 - x1) * 0.66 + random.uniform(offset_min, offset_max)
    cy2 = y1 + (y2 - y1) * 0.66 + random.uniform(offset_min, offset_max)

    points: list[Tuple[float, float]] = []
    for i in range(num_points):
        t = i / (num_points - 1)
        # Cubic Bezier formula: B(t) = (1-t)^3*P0 + 3(1-t)^2*t*P1 + 3(1-t)*t^2*P2 + t^3*P3
        u = 1.0 - t
        tt = t * t
        uu = u * u
        uuu = uu * u
        ttt = tt * t

        x = uuu * x1 + 3.0 * uu * t * cx1 + 3.0 * u * tt * cx2 + ttt * x2
        y = uuu * y1 + 3.0 * uu * t * cy1 + 3.0 * u * tt * cy2 + ttt * y2
        points.append((x, y))

    return points


class MouseController:
    """Controller for human-like mouse movements, clicks, and drags."""

    @staticmethod
    def move_to(
        x: int,
        y: int,
        duration: Optional[float] = None,
        steps: int = 40,
    ) -> None:
        """Move the mouse cursor to target coordinates along a natural Bezier curve.

        Args:
            x: Target X coordinate.
            y: Target Y coordinate.
            duration: Total duration of movement in seconds. If None, randomized.
            steps: Number of interpolation points along the trajectory.

        Raises:
            AutomationError: If mouse movement fails.
        """
        try:
            current_x, current_y = pyautogui.position()
            start = (float(current_x), float(current_y))
            target = (float(x), float(y))

            if duration is None:
                dist = math.hypot(target[0] - start[0], target[1] - start[1])
                # Scale duration with distance (e.g., ~0.1s to 0.6s)
                duration = max(0.15, min(0.6, dist / 800.0 + random.uniform(0.05, 0.15)))

            path = generate_bezier_curve(start, target, num_points=steps)
            step_duration = duration / max(1, len(path))

            for px, py in path:
                pyautogui.moveTo(int(px), int(py))
                # Micro delay for human-like acceleration/deceleration rhythm
                time.sleep(max(0.001, step_duration * random.uniform(0.8, 1.2)))

            # Final snap to exact target
            pyautogui.moveTo(x, y)
            actual_x, actual_y = pyautogui.position()
            logger.debug(
                "MouseController.move_to target=(%d, %d) actual reported "
                "position=(%d, %d)",
                x, y, actual_x, actual_y,
            )
        except Exception as e:
            raise AutomationError(
                f"Failed to move mouse to ({x}, {y})", details=str(e)
            ) from e

    @staticmethod
    def click(
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
    ) -> None:
        """Click at current position or move to (x, y) and click with natural delays.

        Args:
            x: Optional X coordinate to click.
            y: Optional Y coordinate to click.
            button: Mouse button ('left', 'right', 'middle').

        Raises:
            AutomationError: If click operation fails.
        """
        logger.debug(
            "MouseController.click invoked with target=(%s, %s), button=%s",
            x, y, button,
        )
        try:
            if x is not None and y is not None:
                MouseController.move_to(x, y)

            sleep_random(mean=0.08, stddev=0.02, min_delay=0.02, max_delay=0.2)
            pyautogui.click(button=button)
            sleep_random(mean=0.1, stddev=0.03, min_delay=0.03, max_delay=0.3)
        except Exception as e:
            raise AutomationError(
                f"Failed to click at ({x}, {y}) with button {button}", details=str(e)
            ) from e

    @staticmethod
    def drag(
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: float = 0.4,
    ) -> None:
        """Drag the mouse from start to end coordinates smoothly.

        Args:
            start_x: Starting X coordinate.
            start_y: Starting Y coordinate.
            end_x: Ending X coordinate.
            end_y: Ending Y coordinate.
            duration: Duration of drag operation in seconds.

        Raises:
            AutomationError: If drag operation fails.
        """
        try:
            MouseController.move_to(start_x, start_y)
            sleep_random(0.05, 0.01, 0.01, 0.1)
            pyautogui.mouseDown()
            sleep_random(0.05, 0.01, 0.01, 0.1)
            MouseController.move_to(end_x, end_y, duration=duration)
            sleep_random(0.05, 0.01, 0.01, 0.1)
            pyautogui.mouseUp()
            sleep_random(0.1, 0.03, 0.03, 0.3)
        except Exception as e:
            raise AutomationError(
                f"Failed to drag from ({start_x}, {start_y}) to ({end_x}, {end_y})",
                details=str(e),
            ) from e

    @staticmethod
    def scroll_down(clicks: int = 3) -> None:
        """Scroll down by specified number of clicks with human-like timing pauses.

        Args:
            clicks: Number of scroll notches to scroll down.

        Raises:
            AutomationError: If scrolling fails.
        """
        try:
            sleep_random(mean=0.05, stddev=0.01, min_delay=0.02, max_delay=0.1)
            pyautogui.scroll(-abs(clicks))
            sleep_random(mean=0.15, stddev=0.04, min_delay=0.05, max_delay=0.3)
        except Exception as e:
            raise AutomationError(
                f"Failed to scroll down {clicks} clicks", details=str(e)
            ) from e
