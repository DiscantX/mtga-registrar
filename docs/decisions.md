# Architecture Decision Records (ADR) — MTGA Collection Exporter

This document records key architectural decisions made for [`MTGA Registrar`](.).

## ADR 1: Object-Oriented Modular Architecture

- **Status:** Accepted
- **Date:** 2026-09-11
- **Context:** The application needs to handle input automation, image recognition, pagination state, and clipboard exporting while running against Nvidia GeForce Now.
- **Decision:** Organize code into distinct modular packages (`automation`, `vision`, `core`, `export`) adhering to strict object-oriented principles.
- **Consequences:** High maintainability, testability, and clear separation of concerns, allowing components (such as mouse movement simulation or diamond detection) to be tested and updated independently.

## ADR 2: Human-Like Automation & Timing

- **Status:** Accepted
- **Date:** 2026-09-11
- **Context:** Bot detection mechanisms may flag instantaneous mouse movements or rigid click intervals during automated card gathering.
- **Decision:** Implement natural mouse curves and randomized variable delays between actions in [`src/automation/`](src/automation/).
- **Consequences:** Reduced risk of detection during cloud-streamed gameplay on GeForce Now.

## ADR 3: Batch Export Strategy (250 Card Limit)

- **Status:** Accepted
- **Date:** 2026-09-11
- **Context:** MTGA decks have a hard limit of 250 cards per deck when exporting via clipboard.
- **Decision:** Chunk card collection into batches of up to 250 cards per deck, repeating the creation, export, and deletion cycle until the entire collection is grabbed.
- **Consequences:** Reliable export mechanism compatible with MTGA limits without memory access.

## ADR 4: Pluggable Tunnelmole & Local Web Server Transfer for GeForce Now Sandboxing

- **Status:** Accepted
- **Date:** 2026-09-11
- **Context:** Nvidia GeForce Now sandbox restricts direct system clipboard access and file transfer from the cloud instance to the user's host environment. However, triggering HTTP links inside the game spawns a fully functional Edge browser with address bar access.
- **Decision:** Implement a pluggable export transfer architecture (`src/export/`) supporting a local Python web server coupled with Tunnelmole (`tmole`) to securely tunnel payloads, alongside native clipboard handling. The in-game Edge browser navigates to the temporary `https://*.tunnelmole.net` address to transmit exported deck data back to the application.
- **Consequences:** Enables reliable export of collection data from sandboxed GeForce Now environments without requiring memory inspection, while maintaining clean separation of concerns and allowing future transfer mechanisms (such as Pastebin) to be swapped in easily.

## ADR 5: Aspect-Ratio Relative Grid Geometry, Mouse Wheel Pagination, and Immediate Deck Cleanup

- **Status:** Accepted
- **Date:** 2026-09-11
- **Context:** Detecting individual cards and navigating the collection via dynamic visual contour detection is computationally heavy and fragile across varying resolutions. Additionally, accumulating temporary export decks clutters the account and interferes with deck search indexing, while spawning multiple browser tabs violates Tunnelmole's single active connection model.
- **Decision:**
  1. **Starting Point & Format Selection:** Establish the **Decks Screen** as the home screen, click `+` (Create Deck), and omit format selection (unselected format defaults to all cards).
  2. **Relative Grid Math:** Calculate card bounding boxes using normalized relative coordinates tailored to screen aspect ratios (16:9: 2x5 or 3x7; 16:10: 2x4 or 3x6) in **List View**.
  3. **Diamond & Infinity Evaluation:** Count white diamonds (owned) vs. grey diamonds (unowned) out of 4 total slots ($X \in [0, 4]$), or add exactly 1 copy if an $\infty$ symbol is present.
  4. **Pagination:** Advance pages via mouse wheel scroll down events rather than button template clicking.
  5. **Immediate Deck Cleanup:** Immediately after clicking **Export Deck** for the newest leftmost `"New Deck"` on the Decks screen, delete the temporary deck (trash can icon -> confirm OK).
  6. **In-Game Browser Lifecycle:** Open the in-game menu (`ESC`), click **"Your Privacy Choices"**, navigate the Edge browser to the Tunnelmole URL (`Ctrl+L`), and close the tab (`Ctrl+W`) immediately after transmission.
- **Consequences:** Provides robust, fast, resolution-aware card scanning, maintains clean deck list state, avoids bot detection, and ensures dependable cloud-to-local data transmission.
