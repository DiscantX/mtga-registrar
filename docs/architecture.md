# Architecture Documentation — MTGA Collection Exporter

## Overview

[`MTGA Registrar`](.) — MTGA Collection Exporter — is engineered to extract a user's complete MTGA card collection when playing via **Nvidia GeForce Now**, where direct file system access or memory inspection is unavailable.

## System Design & Modules

The application follows strict object-oriented design principles and is divided into modular components located in [`src/`](src/):

1. **Input Automation (`src/automation/`)**
   - Handles mouse and keyboard interaction.
   - Implements human-like movement curves (Bezier curves or variable speed interpolation) and randomized click delays to prevent anti-cheat / bot detection.
   - Manages browser navigation for tunneling workflows when interacting with web-based transfer tools.

2. **Image Recognition & UI Perception (`src/vision/`)**
   - Captures screen regions or window handles.
   - Detects ownership indicators (white outlined diamonds indicating card count).
   - Identifies UI navigation elements (scroll arrows, deck creation buttons, export options).

3. **State & Collection Management (`src/core/`)**
   - Manages pagination, scrolling, and tracking of processed cards.
   - Batches cards into chunks of up to 250 cards per deck (matching MTGA deck limits).

4. **Export & Transfer Handler (`src/export/`)**
   - Provides a pluggable transfer interface supporting multiple backend implementations.
   - **Local Clipboard Provider:** Interacts directly with the system clipboard when running natively.
   - **Tunnelmole Local Web Server Provider:** Bypasses Nvidia GeForce Now sandboxing restrictions by spinning up a thin local HTTP server, tunneling it securely via Tunnelmole (`tmole`), and directing the GeForce Now Edge browser to paste and transmit exported decklists back to the local Python application.
   - Parses exported decklists into structured Python objects or JSON data.

## Workflow Sequence

1. **Initialization:** Connect to the MTGA window running inside GeForce Now.
2. **Deck Setup:** Navigate to decks, create a new deck in "Timeless" format.
3. **Collection Iteration:**
   - Scan current view for owned cards using [`src/vision/`](src/vision/) vision modules.
   - Determine quantity from white outlined diamonds.
   - Add cards programmatically using human-like input automation [`src/automation/`](src/automation/).
   - Scroll or click next page when screen is full.
4. **Batch Export & Tunnel Transfer:**
   - When reaching 250 cards (or end of collection), trigger deck export.
   - Spin up local server and Tunnelmole tunnel (if running under GeForce Now sandbox).
   - Direct the in-game Edge browser to the temporary `https://*.tunnelmole.net` URL to transmit clipboard contents back to the local script.
   - Repeat until all cards are grabbed.
