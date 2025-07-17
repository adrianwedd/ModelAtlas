# Task 201: Implement Centralized Configuration

**Status:** Done

**Description:** Refactored configuration management to use a single, unified `Config` object loaded from a `.env` file.

**Key Changes:**
- Created `atlas_schemas/config.py` with a Pydantic-based `Config` class.
- Configured `Config` to load settings from a `.env` file and provide sane defaults.
- Refactored `enrich/main.py`, `trustforge/score.py`, `tools/scrape_hf.py`, `tools/scrape_ollama.py`, and `tools/enrich_metadata.py` to import and use the `settings` singleton from `atlas_schemas.config`.
- Replaced hardcoded paths and `os.environ` calls with references to `settings` attributes.
- Updated `tests/test_scrape_ollama.py` to correctly use the new `settings` object for test setup.

**Verification:**
- All refactored scripts execute successfully without errors or warnings.
- `tests/test_scrape_ollama.py` passes, confirming correct integration of the new configuration.
