# Changelog — MTGA Collection Exporter

All notable changes to [`MTGA Registrar`](.) will be documented in this file.

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
