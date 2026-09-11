"""Screen capture utility for MTGA Registrar.

Provides robust screen capture functionality using pyautogui/PIL and OpenCV,
supporting full screen and region-based captures with error handling.
"""

import logging
from typing import Optional, Tuple

import numpy as np
import pyautogui  # type: ignore[import-untyped]
from PIL import Image

from src.core.exceptions import VisionError

logger = logging.getLogger("mtga_registrar.vision.capture")


class ScreenCapture:
    """Utility class for capturing screenshots of the MTGA interface."""

    @staticmethod
    def capture_screen(
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> np.ndarray:
        """Capture the screen or a specific region as an OpenCV BGR numpy array.

        Args:
            region: Optional bounding box tuple (left, top, width, height).

        Returns:
            NumPy array representing the captured image in BGR format.

        Raises:
            VisionError: If screen capture fails.
        """
        try:
            logger.debug("Capturing screen with region=%s", region)
            pil_img: Image.Image = pyautogui.screenshot(region=region)
            # Convert PIL RGB image to OpenCV BGR numpy array
            rgb_array = np.array(pil_img)
            bgr_array: np.ndarray = rgb_array[:, :, ::-1].copy()
            return bgr_array
        except Exception as e:
            logger.error("Failed to capture screen: %s", e, exc_info=True)
            raise VisionError(
                f"Screen capture failed: {e}", details=str(e)
            ) from e
