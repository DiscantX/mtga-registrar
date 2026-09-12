# UI Templates

Place calibrated template PNG images here using these exact filenames. Each is loaded
automatically by `TemplateDetector` (see `src/vision/detector.py`) if present; if a file
is missing, the app logs a debug message and falls back to heuristic pixel-ratio detection.

Template matching is used ONLY for the card ownership diamond and infinity indicators,
since those require actual visual identification (owned vs. unowned, or infinite) rather
than a fixed screen position. Every other UI element (buttons, search bar, links) is
resolved directly from calibrated positions in `config/ui_locations.json` and does not
use template matching at all.

- `diamond_white.png`
- `diamond_grey.png`
- `symbol_infinity.png`