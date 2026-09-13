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
from src.core.ui_locations import get_location

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

    @staticmethod
    def calculate_card_grid(
        image_shape: Tuple[int, ...],
        zoom_level: int = 2,
    ) -> List[Tuple[int, int, int, int]]:
        """Calculate aspect-ratio-aware card slot bounding boxes for List View.

        Supports 16:9 (1920x1080) and 16:10 (1920x1200) aspect ratios.
        - 16:9 (ar ≈ 1.778):
          - zoom_level == 2 (standard): 2 rows × 5 columns = 10 slots.
          - zoom_level == 3 (zoomed out): 3 rows × 7 columns = 21 slots.
        - 16:10 (ar ≈ 1.6):
          - zoom_level == 2 (standard): 2 rows × 4 columns = 8 slots.
          - zoom_level == 3 (zoomed out): 3 rows × 6 columns = 18 slots.

        For zoom_level == 2, slot geometry is derived from the hand-calibrated
        "playmat" (outer grid viewport) and "example_card" (single card slot
        size) entries in config/ui_locations.json, rather than fabricated
        percentage margins.

        For zoom_level == 3, no calibration data exists yet, so the original
        fabricated percentage-margin math is retained unchanged until a
        "deck_editor_screen_3" playmat/example_card calibration is added.

        Args:
            image_shape: (height, width) tuple of the screen or viewport image.
            zoom_level: Collection view zoom level (default 2).

        Returns:
            List of (x, y, width, height) bounding boxes for each card slot.

        Raises:
            VisionError: If image shape is invalid.
        """
        try:
            if (
                not image_shape
                or len(image_shape) < 2
                or image_shape[0] <= 0
                or image_shape[1] <= 0
            ):
                raise VisionError(
                    "Invalid image shape provided for grid calculation."
                )

            h, w = image_shape[:2]
            aspect_ratio = float(w) / float(h)

            # Determine grid dimensions based on aspect ratio and zoom level
            if aspect_ratio >= 1.7:
                ar_key = "16:9"
                if zoom_level == 3:
                    rows, cols = 3, 7
                else:
                    rows, cols = 2, 5
            else:
                ar_key = "16:10"
                if zoom_level == 3:
                    rows, cols = 3, 6
                else:
                    rows, cols = 2, 4

            grid_boxes: List[Tuple[int, int, int, int]] = []

            if zoom_level == 3:
                # UNCALIBRATED: zoom level 3 has no "playmat"/"example_card"
                # reference for a 3-row view yet, so this fabricated
                # percentage-margin math is retained until that calibration
                # is captured. Do not treat these numbers as trustworthy.
                left_margin = int(w * 0.08)
                right_margin = int(w * 0.08)
                top_margin = int(h * 0.22)
                bottom_margin = int(h * 0.15)

                available_width = w - left_margin - right_margin
                available_height = h - top_margin - bottom_margin

                if available_width <= 0 or available_height <= 0:
                    raise VisionError(
                        "Calculated available grid area is non-positive."
                    )

                col_width = available_width / cols
                row_height = available_height / rows

                for r in range(rows):
                    for c in range(cols):
                        slot_x = left_margin + int(c * col_width)
                        slot_y = top_margin + int(r * row_height)
                        slot_w = int(col_width)
                        slot_h = int(row_height)
                        grid_boxes.append((slot_x, slot_y, slot_w, slot_h))
            else:
                # Calibrated zoom level 2 grid, using playmat (outer bounds)
                # and example_card (slot width/height) from ui_locations.json.
                pm_x, pm_y, pm_w, pm_h = get_location("playmat", w, h, ar_key)
                _, _, card_w, card_h = get_location(
                    "example_card", w, h, ar_key
                )

                if cols <= 1 or rows <= 1:
                    raise VisionError(
                        "Calibrated grid math requires at least 2 rows and "
                        "2 columns."
                    )

                h_margin = (pm_w - card_w * cols) / (cols - 1)
                v_margin = (pm_h - card_h * rows) / (rows - 1)
                step_x = card_w + h_margin
                step_y = card_h + v_margin

                for r in range(rows):
                    for c in range(cols):
                        slot_x = int(pm_x + c * step_x)
                        slot_y = int(pm_y + r * step_y)
                        grid_boxes.append((slot_x, slot_y, card_w, card_h))

            logger.debug(
                "Calculated %d card slots for ar=%.3f (zoom=%d): %dx%d grid",
                len(grid_boxes), aspect_ratio, zoom_level, rows, cols
            )
            return grid_boxes

        except Exception as e:
            if isinstance(e, VisionError):
                raise e
            logger.error("Grid geometry calculation failed: %s", e, exc_info=True)
            raise VisionError(
                f"Grid calculation error: {e}", details=str(e)
            ) from e

    @staticmethod
    def evaluate_card_ownership(card_slot_image: np.ndarray) -> int:
        """Evaluate card ownership quantity from a card slot image.

        Crops the top header region of the card slot where the 4 diamond indicators
        and/or infinity symbol reside. Analyzes sub-regions for the 4 diamonds
        (bright white = 1, dark grey = 0) and checks for an infinity symbol (returns 1).

        Args:
            card_slot_image: BGR numpy array representing a single card slot.

        Returns:
            Owned quantity X in range [0, 4].

        Raises:
            VisionError: If image shape is invalid.
        """
        try:
            if (
                card_slot_image is None
                or card_slot_image.size == 0
                or len(card_slot_image.shape) < 2
            ):
                raise VisionError("Invalid card slot image provided for ownership evaluation.")

            h, w = card_slot_image.shape[:2]

            # Crop top header region where ownership indicators (diamonds / infinity) reside
            header_ymin = int(h * 0.02)
            header_ymax = int(h * 0.28)
            header_xmin = int(w * 0.1)
            header_xmax = int(w * 0.9)

            header_region = card_slot_image[header_ymin:header_ymax, header_xmin:header_xmax]
            if header_region.size == 0:
                return 0

            # Convert to grayscale
            if len(header_region.shape) == 3:
                gray = cv2.cvtColor(header_region, cv2.COLOR_BGR2GRAY)
            else:
                gray = header_region

            hr_h, hr_w = gray.shape[:2]

            # 1. Check for infinity symbol
            _, bin_img = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(bin_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if 20 <= area <= 1000:
                    _, _, c_w, c_h = cv2.boundingRect(cnt)
                    aspect_ratio = float(c_w) / c_h if c_h > 0 else 0
                    if 1.2 <= aspect_ratio <= 3.0 and hr_w * 0.2 <= c_w <= hr_w * 0.9:
                        logger.debug("Detected infinity symbol contour, returning quantity 1.")
                        return 1

            # 2. Evaluate 4 diamond indicators horizontally spaced across the header region
            segment_width = hr_w / 4.0
            total_diamonds = 0

            for i in range(4):
                seg_x1 = int(i * segment_width)
                seg_x2 = int((i + 1) * segment_width)
                diamond_seg = gray[:, seg_x1:seg_x2]

                if diamond_seg.size == 0:
                    continue

                bright_pixels = np.sum(diamond_seg > 200)
                total_pixels = diamond_seg.size
                bright_ratio = float(bright_pixels) / total_pixels

                if bright_ratio >= 0.05:
                    total_diamonds += 1

            quantity = min(max(total_diamonds, 0), 4)
            logger.debug("Evaluated card ownership quantity: %d", quantity)
            return quantity

        except Exception as e:
            if isinstance(e, VisionError):
                raise e
            logger.error("Card ownership evaluation failed: %s", e, exc_info=True)
            raise VisionError(
                f"Card ownership evaluation error: {e}", details=str(e)
            ) from e
