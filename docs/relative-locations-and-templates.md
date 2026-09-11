# Relative Locations, UI Coordinates & Template Matching Audit

This document provides a comprehensive inventory of all fabricated/heuristic locations, relative coordinates, outer margins, inter-card gaps, and UI element bounding boxes in [`MTGA Registrar`](.), as well as a complete template matching analysis and catalog of missing image templates.

---

## 1. Inventory of Fabricated Locations & Relative Coordinates

### 1.1 Card Grid Viewport & Inter-Card Margins
In [`TemplateDetector.calculate_card_grid()`](src/vision/detector.py:185) ([`src/vision/detector.py`](src/vision/detector.py)):
- **Fabricated Outer Viewport Margins:**
  - `left_margin = int(w * 0.08)` ([`src/vision/detector.py:238`](src/vision/detector.py:238))
  - `right_margin = int(w * 0.08)` ([`src/vision/detector.py:239`](src/vision/detector.py:239))
  - `top_margin = int(h * 0.22)` ([`src/vision/detector.py:240`](src/vision/detector.py:240))
  - `bottom_margin = int(h * 0.15)` ([`src/vision/detector.py:241`](src/vision/detector.py:241))
- **Confirmed Grid Divisions (Correct):**
  - **16:9 aspect ratio:** `2 rows × 5 cols` (zoom level 2) / `3 rows × 7 cols` (zoom level 3) ([`src/vision/detector.py:227`](src/vision/detector.py:227))
  - **16:10 aspect ratio:** `2 rows × 4 cols` (zoom level 2) / `3 rows × 6 cols` (zoom level 3) ([`src/vision/detector.py:233`](src/vision/detector.py:233))
- **Inter-Card Margins & Spacing Math Requirements:**
  - **Outer Card Area Boundaries:** Normalized percentages for top, bottom, left, and right grid edges.
  - **Inter-Card Horizontal Gap:** Normalized gap or padding percentage between adjacent columns ($Gap_x$).
  - **Inter-Card Vertical Gap:** Normalized gap or padding percentage between adjacent rows ($Gap_y$).
  - **Card Slot Dimensions / Aspect Ratio:** Calculated via math once outer bounds, row/column counts, and inter-card margins are provided:
    $$W_{slot} = \frac{W_{available} - (Cols - 1) \times Gap_x}{Cols}$$
    $$H_{slot} = \frac{H_{available} - (Rows - 1) \times Gap_y}{Rows}$$

### 1.2 Card Slot Header & Ownership Indicator Sub-Regions
In [`TemplateDetector.evaluate_card_ownership()`](src/vision/detector.py:276) ([`src/vision/detector.py`](src/vision/detector.py)):
- **Fabricated Sub-Crop Region:**
  - `header_ymin = int(h * 0.02)` (top 2% of slot) ([`src/vision/detector.py:303`](src/vision/detector.py:303))
  - `header_ymax = int(h * 0.28)` (top 28% of slot) ([`src/vision/detector.py:304`](src/vision/detector.py:304))
  - `header_xmin = int(w * 0.10)` (left 10% of slot) ([`src/vision/detector.py:305`](src/vision/detector.py:305))
  - `header_xmax = int(w * 0.90)` (right 90% of slot) ([`src/vision/detector.py:306`](src/vision/detector.py:306))
- **Fabricated Slicing & Thresholds:**
  - Equal 4-way segment slice: `segment_width = hr_w / 4.0` ([`src/vision/detector.py:334`](src/vision/detector.py:334))
  - Bright pixel ratio filter: `bright_pixels = np.sum(diamond_seg > 200)` ([`src/vision/detector.py:345`](src/vision/detector.py:345))
- **Fabricated Infinity Contour Rules:**
  - Contour area `20 <= area <= 1000` ([`src/vision/detector.py:326`](src/vision/detector.py:326))
  - Aspect ratio `1.2 <= aspect_ratio <= 3.0` ([`src/vision/detector.py:329`](src/vision/detector.py:329))
- **Research Needed:**
  - Exact bounding box/offset for 4-diamond indicator cluster relative to card slot.
  - Template reference crops for white (owned) vs. grey (unowned) diamonds and infinity ($\infty$) symbol.

### 1.3 Standalone Ownership Diamond Heuristics
In [`TemplateDetector.detect_ownership_diamonds()`](src/vision/detector.py:112) ([`src/vision/detector.py`](src/vision/detector.py)):
- Binary threshold: [`cv2.threshold(gray, 210, 255, cv2.THRESH_BINARY)`](src/vision/detector.py:150)
- Contour area filter: [`10 <= area <= 500`](src/vision/detector.py:158)
- Aspect ratio filter: [`0.5 <= aspect_ratio <= 2.0`](src/vision/detector.py:161)

### 1.4 UI Element Bounding Boxes in [`UIDetector`](src/vision/ui.py:19)
In [`src/vision/ui.py`](src/vision/ui.py):
- **`+` (Create Deck) Button:** `(int(w * 0.15), int(h * 0.15), 140, 50)` ([`src/vision/ui.py:133`](src/vision/ui.py:133))
- **Decks Search Bar:** `(int(w * 0.70), int(h * 0.12), 200, 40)` ([`src/vision/ui.py:214`](src/vision/ui.py:214))
- **Leftmost Deck Card Slot:** `(int(w * 0.15), int(h * 0.30), 180, 220)` ([`src/vision/ui.py:250`](src/vision/ui.py:250))
- **Export Deck Button:** `(int(w * 0.25), int(h * 0.90), 120, 40)` ([`src/vision/ui.py:97`](src/vision/ui.py:97))
- **Delete / Trash Can Icon:** `(int(w * 0.85), int(h * 0.15), 50, 50)` ([`src/vision/ui.py:286`](src/vision/ui.py:286))
- **Confirmation Dialogue OK Button:** `(int(w * 0.55), int(h * 0.60), 120, 45)` ([`src/vision/ui.py:322`](src/vision/ui.py:322))
- **"Your Privacy Choices" Link:** `(int(w * 0.50), int(h * 0.85), 220, 40)` ([`src/vision/ui.py:358`](src/vision/ui.py:358))
- **Format Selector Dropdown:** `(int(w * 0.50), int(h * 0.30), 160, 45)` ([`src/vision/ui.py:175`](src/vision/ui.py:175))
- **Pagination Navigation Arrows:** `(int(w * 0.85), int(h * 0.85), 60, 60)` ([`src/vision/ui.py:56`](src/vision/ui.py:56))

### 1.5 Hardcoded Absolute Click Coordinates in Automation Workflows
In [`src/core/app.py`](src/core/app.py) & [`src/automation/browser.py`](src/automation/browser.py):
- **Done / Save Deck Button:** [`MouseController.click(1850, 50)`](src/core/app.py:274) in [`ApplicationController.save_current_deck()`](src/core/app.py:270)
- **Fallback Search Bar Click:** [`MouseController.click(1400, 130)`](src/core/app.py:299) in [`ApplicationController.export_and_cleanup_deck()`](src/core/app.py:288)
- **Fallback Leftmost Deck Click:** [`MouseController.click(300, 300)`](src/core/app.py:314) in [`ApplicationController.export_and_cleanup_deck()`](src/core/app.py:288)
- **Fallback Export Button Click:** [`MouseController.click(500, 950)`](src/core/app.py:324) in [`ApplicationController.export_and_cleanup_deck()`](src/core/app.py:288)
- **Fallback Trash Can Click:** [`MouseController.click(1650, 150)`](src/core/app.py:334) in [`ApplicationController.export_and_cleanup_deck()`](src/core/app.py:288)
- **Fallback Confirm OK Click:** [`MouseController.click(1050, 650)`](src/core/app.py:344) in [`ApplicationController.export_and_cleanup_deck()`](src/core/app.py:288)
- **Fallback "Your Privacy Choices" Click:** [`MouseController.click(960, 900)`](src/automation/browser.py:123) in [`BrowserController.open_privacy_browser()`](src/automation/browser.py:103)

---

## 2. Template Matching Analysis & Missing Templates Catalog

### 2.1 Current State of Template Matching
- **OpenCV Engine:** [`TemplateDetector.match_template()`](src/vision/detector.py:23) is implemented using [`cv2.matchTemplate(..., cv2.TM_CCOEFF_NORMED)`](src/vision/detector.py:73).
- **Function Parameters:** Every function in [`UIDetector`](src/vision/ui.py:19) accepts `template: Optional[np.ndarray] = None`.
- **Usage Gap:** No template image assets exist in the workspace, and no template loader is wired to [`ApplicationController`](src/core/app.py:29). Thus, `template` is always `None` during execution, causing the application to execute heuristic fallback branches.

### 2.2 Catalog of Required Templates

| Reference Image Name | Description / Target UI Element | Purpose | Associated Function |
| :--- | :--- | :--- | :--- |
| `btn_create_deck.png` | `+` (Create Deck) button on Decks screen | Navigates from home screen to Deck Builder | [`UIDetector.find_deck_creation_button()`](src/vision/ui.py:106) |
| `btn_done.png` | "Done" / Save Deck button | Saves deck and exits builder | [`ApplicationController.save_current_deck()`](src/core/app.py:270) |
| `btn_export.png` | "Export" / "Export Deck" button | Copies decklist to GFN clipboard | [`UIDetector.find_export_button()`](src/vision/ui.py:70) |
| `btn_trash.png` | Trash can / Delete icon | Deletes temporary batch deck | [`UIDetector.find_trash_can_button()`](src/vision/ui.py:259) |
| `btn_confirm_ok.png` | "OK" confirmation button | Dismisses dialogs and confirms deletion | [`UIDetector.find_confirmation_ok_button()`](src/vision/ui.py:295) |
| `input_search_bar.png` | Decks search bar / Search icon | Focuses search box for `"New Deck"` | [`UIDetector.find_decks_search_bar()`](src/vision/ui.py:187) |
| `link_privacy_choices.png` | "Your Privacy Choices" link text | Launches Edge browser in ESC menu | [`UIDetector.find_privacy_choices_link()`](src/vision/ui.py:331) |
| `diamond_white.png` | White diamond pip (owned copy) | Validates owned card copy ($1-4$) | [`TemplateDetector.detect_ownership_diamonds()`](src/vision/detector.py:112) |
| `diamond_grey.png` | Grey diamond pip (unowned copy) | Distinguishes unowned slot | [`TemplateDetector.evaluate_card_ownership()`](src/vision/detector.py:276) |
| `symbol_infinity.png` | Infinity ($\infty$) symbol | Handles basic land infinite quantity ($X=1$) | [`TemplateDetector.evaluate_card_ownership()`](src/vision/detector.py:276) |
| `btn_list_view.png` | List View toggle icon | Ensures deck builder is in List View | UI Verification |
