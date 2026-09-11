# Changelog — MTGA Collection Exporter

All notable changes to [`MTGA Registrar`](.) will be documented in this file.

## [0.4.0] - 2026-09-11

### Added
- **Relative Locations & Template Audit**: Added [`docs/relative-locations-and-templates.md`](docs/relative-locations-and-templates.md) detailing all fabricated relative coordinates, inter-card margin math, heuristic fallback clicks, template matching analysis, and missing image templates catalog.
- **Real-World Execution Lifecycle**: Specified the complete concrete workflow in [`docs/architecture.md`](docs/architecture.md), starting from the Decks screen, creating a deck without format restrictions, and processing batches up to 250 cards.
- **Aspect-Ratio Relative Grid Geometry**: Documented relative normalized coordinate math for card detection across 16:9 (2x5 and 3x7) and 16:10 (2x4 and 3x6) aspect ratios in List View.
- **Diamond State & Infinity Recognition**: Documented 4-diamond slot evaluation (white owned vs. grey empty) and the infinity ($\infty$) symbol handling rule (add exactly 1 card).
- **Mouse Wheel Pagination**: Replaced navigation button dependencies with mouse wheel scroll down automation.
- **Deck Cleanup Automation**: Added immediate deck deletion (trash can icon -> confirm dialogue) following decklist export on the Decks screen.
- **Privacy Link Browser Tunneling Lifecycle**: Documented ESC menu navigation to "Your Privacy Choices", address bar focus (`Ctrl+L`), and subsequent tab closure (`Ctrl+W`) to enforce Tunnelmole single-connection constraints.
- **Architecture Decision Record (ADR 5)**: Added ADR 5 in [`docs/decisions.md`](docs/decisions.md) detailing grid geometry, scroll wheel pagination, deck cleanup, and browser lifecycle.

## [0.3.0] - 2026-09-11

### Added
- **Application Controller (`src/core/app.py`)**: Implemented the main application controller orchestrating vision, automation, state management, pagination, batching, and export transfer handlers into a cohesive collection export workflow.
- **CLI Entry Point (`main.py`)**: Implemented command-line argument parsing supporting dry-run mode, log level configuration, max batch size, and transfer mode selection (`clipboard`, `server`, `tunnelmole`).
- **Integration Tests (`tests/test_integration.py`)**: Implemented comprehensive integration tests verifying end-to-end collection export workflows, dry-run mode, deck creation failure handling, and large collection batching (>250 cards).
- **Documentation Updates**: Updated [`docs/changelog.md`](docs/changelog.md) and [`docs/architecture.md`](docs/architecture.md).

## [0.2.0] - 2026-09-11

### Added
- **Tunnelmole & Local Web Server Transfer (`src/export/`)**: Added Phase 5 to [`plans/execution_plan.md`](plans/execution_plan.md) to implement a pluggable export transfer mechanism utilizing a local Python web server and Tunnelmole (`tmole`) to bypass Nvidia GeForce Now sandbox clipboard limitations.
- **Architecture Documentation Updates**: Updated [`docs/architecture.md`](docs/architecture.md) to document the pluggable transfer handler supporting both native system clipboard and Tunnelmole-backed browser transfer.
- **Architecture Decision Record (ADR 4)**: Recorded ADR 4 in [`docs/decisions.md`](docs/decisions.md) detailing the rationale and design for Tunnelmole integration in sandboxed cloud gaming environments.

## [0.1.0] - 2026-09-11

### Added
- Initial project setup and repository structure.
- Documentation for AI assistants ([`CLAUDE.md`](CLAUDE.md) and [`AGENTS.md`](AGENTS.md)).
- Architecture design documentation ([`docs/architecture.md`](docs/architecture.md)).
- Changelog ([`docs/changelog.md`](docs/changelog.md)) and Architecture Decision Records ([`docs/decisions.md`](docs/decisions.md)).
- Modular object-oriented architecture plan for automation, vision, state management, and clipboard export.
