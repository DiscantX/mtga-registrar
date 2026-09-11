"""Template image loading and caching for MTGA Registrar.

Loads calibrated reference template PNGs from the `templates/` directory at the
project root, if present. Provides graceful fallback (returns None + logs a
warning) when a template file has not yet been supplied by a human.
"""

import logging
import os
from typing import Dict, Optional

import cv2
import numpy as np

logger = logging.getLogger("mtga_registrar.vision.templates")


class TemplateLibrary:
    """Loads and caches UI template images from the `templates/` directory."""

    _TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "templates")
    _cache: Dict[str, Optional[np.ndarray]] = {}

    @classmethod
    def load(cls, filename: str) -> Optional[np.ndarray]:
        """Load a template image by filename from the templates/ directory.

        Results are cached after the first lookup (including negative lookups).

        Args:
            filename: Template filename, e.g. "btn_export.png".

        Returns:
            The loaded BGR numpy image array, or None if the file does not
            exist or could not be read. A warning is logged in that case.
        """
        if filename in cls._cache:
            return cls._cache[filename]

        path = os.path.join(cls._TEMPLATE_DIR, filename)
        if not os.path.isfile(path):
            logger.warning(
                "Template '%s' not found at %s; falling back to heuristic detection.",
                filename, path,
            )
            cls._cache[filename] = None
            return None

        image = cv2.imread(path, cv2.IMREAD_COLOR)
        if image is None:
            logger.warning("Template '%s' exists but could not be read as an image.", filename)
        cls._cache[filename] = image
        return image
