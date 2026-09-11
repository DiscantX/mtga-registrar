# AGENTS.md - Multi-Agent Guidelines & Protocol

This document outlines operational guidelines for AI agents working within the [`mtga-registrar`](.) repository.

## Project Mission & Context

[`MTGA Registrar`](.) — MTGA Collection Exporter — solves the problem of exporting a user's full MTGA collection when playing via **Nvidia GeForce Now** (where direct file/memory access is unavailable).

### Core Operational Strategy & Lifecycle

1. **Home Screen & Deck Creation:** Start from the **Decks Screen** (home). Click `+` (Create Deck). Format selection is omitted (unselected format displays all collection cards).
2. **List View & Aspect-Ratio Grid Math:** Operate in **List View**. Calculate card bounding boxes via normalized relative coordinates for 16:9 (2x5 or 3x7) and 16:10 (2x4 or 3x6) aspect ratios.
3. **Card Automation & Ownership Detection:** Evaluate the 4-diamond cluster above each card (white = owned, grey = empty) to determine quantity $X \in [0, 4]$. For special cards with an infinity ($\infty$) symbol, add exactly 1 copy ($X = 1$). Click each card slot $X$ times using human-like Bezier curves and variable click intervals.
4. **Pagination:** Advance through the collection using mouse wheel scroll down events (`MouseController.scroll_down`).
5. **Batching & Deck Limit (250 Cards):** When reaching 250 cards (or end of collection), save the deck, dismiss the "Too Many Cards" popup, and return to the Decks screen.
6. **Deck Selection, Export & Immediate Cleanup:** Search `"New Deck"` in the search bar, click the leftmost (newest) deck, click **Export Deck** (copies decklist to GFN clipboard), and immediately delete the deck (trash can icon -> confirm OK).
7. **Cloud Sandbox Transfer via Tunnelmole:** Press `ESC`, click **"Your Privacy Choices"** to open Edge, focus the address bar (`Ctrl+L`), type the Tunnelmole URL (`https://*.tunnelmole.net`), send the clipboard payload to the local server, and close the tab (`Ctrl+W`) to preserve single-connection limits.
8. **Human-Like Interaction:** Prevent bot detection by ensuring natural mouse movement curves, variable click delays, and non-instantaneous transitions.

## Agent Responsibilities & Standards

1. **Architecture & Modularity:**
   - Follow strict object-oriented programming principles with modular components (input automation, image recognition, state management, clipboard handling).
   - Document all modules, classes, and functions with comprehensive docstrings.
2. **Documentation Maintenance:**
   - Keep [`docs/architecture.md`](docs/architecture.md) updated with system design.
   - Record key architectural decisions in [`docs/decisions.md`](docs/decisions.md).
   - Log progress and changes in [`docs/changelog.md`](docs/changelog.md).
   - Ensure all markdown/document links across all `.md` files are strictly relative to the project root (e.g., [`docs/architecture.md`](docs/architecture.md)).
3. **Verification:**
   - Run tests (`pytest`) and type/lint checks (`mypy .`, `ruff check .`) before concluding tasks.

## Build & Test Commands

- **Run tests:** `pytest`
- **Run linter / static analysis:** `flake8` or `ruff check .`
- **Type checking:** `mypy .`
- **Run application:** `python main.py` (or appropriate entry point)

## Code Style & Conventions

- **Language:** Python 3.10+
- **Style Guide:** PEP 8 compliance, clear type annotations on all public functions/methods.
- **Documentation:** Google-style docstrings for modules, classes, and functions.
- **Error Handling:** Explicit exception handling with custom domain exceptions where appropriate; avoid bare `except:` clauses.
- **Testing:** Unit tests using `pytest` with high coverage for core parsing and extraction logic.

## Project Structure

- [`src/`](src/) - Source code directory.
- [`tests/`](tests/) - Test suite.
- [`docs/`](docs/) - Project documentation, architecture notes, decisions, and changelogs.
- [`AGENTS.md`](AGENTS.md) - Multi-agent collaboration guidelines.
- [`CLAUDE.md`](CLAUDE.md) - Claude collaboration guidelines.
