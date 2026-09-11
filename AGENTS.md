# AGENTS.md - Multi-Agent Guidelines & Protocol

This document outlines operational guidelines for AI agents working within the [`mtga-registrar`](.) repository.

## Project Mission & Context

[`MTGA Registrar`](.) — MTGA Collection Exporter — solves the problem of exporting a user's full MTGA collection when playing via **Nvidia GeForce Now** (where direct file/memory access is unavailable).

### Core Strategy

1. **Deck Creation:** Create a new deck in the "Timeless" format (maximum permissiveness).
2. **Card Automation:** Programmatically add cards based on ownership indicators (white outlined diamonds indicating quantity owned).
3. **Screen Navigation:** Scroll through card pages using predictable math or UI element detection for the right arrow button.
4. **Export & Batching:** Utilize the built-in "export deck" feature (clipboard copy) in batches of up to 250 cards per deck, repeating until the entire collection is grabbed.
5. **Human-Like Interaction:** Prevent bot detection by ensuring natural mouse movement curves, variable click delays, and non-instantaneous transitions.

## Agent Responsibilities & Standards

1. **Architecture & Modularity:**
   - Follow strict object-oriented programming principles with modular components (input automation, image recognition, state management, clipboard handling).
   - Document all modules, classes, and functions with comprehensive docstrings.
2. **Documentation Maintenance:**
   - Keep [`docs/architecture.md`](docs/architecture.md) updated with system design.
   - Record key architectural decisions in [`docs/decisions.md`](docs/decisions.md).
   - Log progress and changes in [`docs/changelog.md`](docs/changelog.md).
   - Ensure all markdown/document links across all `.md` files are strictly relative to the project root (e.g., [`architecture.md`](docs/architecture.md)).
3. **Verification:**
   - Run tests (`[`pytest`](pytest)`) and type/lint checks (`[`mypy .`](mypy .)`, `[`ruff check .`](ruff check .)`) before concluding tasks.

## Build & Test Commands

- **Run tests:** [`pytest`](pytest)
- **Run linter / static analysis:** [`flake8`](flake8) or [`ruff check .`](ruff check .)
- **Type checking:** [`mypy .`](mypy .)
- **Run application:** [`python main.py`](main.py) (or appropriate entry point)

## Code Style & Conventions

- **Language:** Python 3.10+
- **Style Guide:** PEP 8 compliance, clear type annotations on all public functions/methods.
- **Documentation:** Google-style docstrings for modules, classes, and functions.
- **Error Handling:** Explicit exception handling with custom domain exceptions where appropriate; avoid bare `except:` clauses.
- **Testing:** Unit tests using [`pytest`](pytest) with high coverage for core parsing and extraction logic.

## Project Structure

- [`src/`](src/) - Source code directory.
- [`tests/`](tests/) - Test suite.
- [`docs/`](docs/) - Project documentation, architecture notes, decisions, and changelogs.
- [`AGENTS.md`](AGENTS.md) - Multi-agent collaboration guidelines.
- [`CLAUDE.md`](CLAUDE.md) - Claude collaboration guidelines.
