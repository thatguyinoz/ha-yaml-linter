# HA YAML Linter - Project Roadmap & TODO

## Phase 1: Project Setup
- [x] Initialize Python virtual environment and dependencies (`ruamel.yaml`, `Flask`, `pytest`).
- [x] Setup base project structure (`src/`, `tests/`, `web/`).
- [x] Create a local memory/workflow tracking document (`.project_workflow.md`).

## Phase 2: Core Indentation & Parser Engine
- [x] Register HA-specific tags (`!include`, `!secret`, `!include_dir_list`, `!include_dir_named`, `!include_dir_merge_list`, `!include_dir_merge_named`) to bypass parser errors.
- [x] Build the first-pass indentation analyzer (scans line-by-line, checks indentation increments, consistency, and alignment).
- [x] Implement the "Most Likely Fix" recommendation engine for common indent bugs (e.g., list items indented too far, mismatched key-value alignment).
- [x] Write robust unit tests for the core parser and suggestion engine.

## Phase 3: CLI Interface
- [x] Support reading files via CLI path arguments.
- [x] Support reading from `stdin` (for user copy-paste directly in terminal).
- [x] Return clean, colored, and readable terminal output showing the exact line, column, and suggestion.

## Phase 4: Web Frontend
- [x] Build a lightweight Flask app to serve the web front end.
- [x] Design a clean, modern, and responsive single-page visual editor.
- [x] Implement side-by-side or inline display of indentation errors, with "Click to Apply" suggestions.
- [x] Support file upload (drag & drop) and direct copy-paste.
- [x] Add line numbers to the display of the uploaded yaml file in the web gui

## Phase 5: Verification & Deployment Documentation
- [x] Create a comprehensive test suite covering edge cases (mixed tabs/spaces, nested lists, multi-line strings).
- [x] Document installation, SCP copy workflow, and server execution guides.

## Phase 6: Mixed Style Detection & Auto-Unification
- [ ] Count and analyze sequence indentation styles (Compact vs. Nested) in the analyzer.
- [ ] Build the Python Indentation Shift Engine to automatically rewrite mixed styles.
- [ ] Add CLI flag `--fix-style` for command-line auto-unification.
- [ ] Add interactive amber warning panel and one-click unification buttons in Web UI.
