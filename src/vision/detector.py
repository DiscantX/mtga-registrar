"""Template matching and detection module for MTGA Registrar.

Provides computer vision algorithms for template matching, locating UI elements,
and detecting card ownership diamonds/quantities.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from src.core.config import settings
from src.core.exceptions import VisionError

logger = logging.getLogger("mtga_registrar.vision.detector")


class TemplateDetector:
    """Performs template matching and visual feature detection on game screenshots."""

    @staticmethod
    def match_template(
        image: np.ndarray,
        template: np.ndarray,
        threshold: float = 0.8,
    ) -> List[Tuple[int, int, int, int, float]]:
        """Match a template image within a larger target image using OpenCV.

        Args:
            image: Target image (BGR numpy array) to search within.
            template: Template image (BGR numpy array) to search for.
            threshold: Minimum confidence score (0.0 to 1.0) for a match.

        Returns:
            List of bounding box tuples: (x, y, width, height, confidence).

        Raises:
            VisionError: If matching fails due to invalid image shapes or types.
        """
        try:
            if (
                image is None
                or template is None
                or image.size == 0
                or template.size == 0
            ):
                raise VisionError(
                    "Invalid image or template provided for matching."
                )

            # Convert to grayscale if channels differ or for robust matching
            if len(image.shape) == 3:
                img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                img_gray = image

            if len(template.shape) == 3:
                tmpl_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            else:
                tmpl_gray = template

            h, w = tmpl_gray.shape[:2]
            img_h, img_w = img_gray.shape[:2]

            if h > img_h or w > img_w:
                logger.warning(
                    "Template dimensions (%dx%d) larger than image (%dx%d)",
                    w, h, img_w, img_h
                )
                return []

            result = cv2.matchTemplate(
                img_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED
            )
            loc = np.where(result >= threshold)

            matches: List[Tuple[int, int, int, int, float]] = []
            seen_boxes: List[Tuple[int, int]] = []

            # Extract matches with non-maximum suppression / deduplication
            for pt in zip(*loc[::-1], strict=False):  # X, Y coordinates
                confidence = float(result[pt[1], pt[0]])
                # Check for proximity to avoid duplicate detections
                is_duplicate = False
                for bx, by in seen_boxes:
                    if (
                        abs(pt[0] - bx) < w // 2
                        and abs(pt[1] - by) < h // 2
                    ):
                        is_duplicate = True
                        break

                if not is_duplicate:
                    seen_boxes.append((pt[0], pt[1]))
                    matches.append((pt[0], pt[1], w, h, confidence))

            logger.debug(
                "Found %d matches at threshold %.2f", len(matches), threshold
            )
            return matches

        except Exception as e:
            if isinstance(e, VisionError):
                raise e
            logger.error("Template matching failed: %s", e, exc_info=True)
            raise VisionError(
                f"Template matching error: {e}", details=str(e)
            ) from e

    @staticmethod
    def detect_ownership_diamonds(
        image: np.ndarray,
        diamond_template: Optional[np.ndarray] = None,
        threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Detect card ownership diamonds (white outlined diamonds) in a card slot.

        Args:
            image: BGR numpy array of the card region or search area.
            diamond_template: Optional template image of a white outlined diamond.
            threshold: Optional confidence threshold.

        Returns:
            List of detected diamond items with coordinates and confidence.
        """
        thresh = threshold or settings.confidence_threshold
        try:
            if diamond_template is not None:
                matches = TemplateDetector.match_template(
                    image, diamond_template, threshold=thresh
                )
                results = []
                for x, y, w, h, conf in matches:
                    results.append({
                        "x": x,
                        "y": y,
                        "width": w,
                        "height": h,
                        "confidence": conf,
                    })
                return results

            # Fallback heuristic color filtering for white/bright outlined shapes
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            _, thresh_img = cv2.threshold(gray, 210, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(
                thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            detected: List[Dict[str, Any]] = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if 10 <= area <= 500:
                    x, y, w, h = cv2.boundingRect(cnt)
                    aspect_ratio = float(w) / h if h > 0 else 0
                    if 0.5 <= aspect_ratio <= 2.0:
                        detected.append({
                            "x": x,
                            "y": y,
                            "width": w,
                            "height": h,
                            "confidence": 0.85,
                        })

            logger.debug(
                "Detected %d ownership diamond indicators via heuristics",
                len(detected)
            )
            return detected

        except Exception as e:
            logger.error(
                "Failed to detect ownership diamonds: %s", e, exc_info=True
            )
            raise VisionError(
                f"Diamond detection failed: {e}", details=str(e)
            ) from e
