# Task 416: Raise error on missing config keys

## Summary
- Added validation to `atlas_schemas.config.Config` to check for required environment variables.
- Instantiation now raises a `ValueError` listing missing keys with guidance to update the `.env` file.
- Created `tests/test_config.py` to cover success and failure scenarios.
- Updated `tests/test_scrape_ollama.py` to set required keys for existing tests.
