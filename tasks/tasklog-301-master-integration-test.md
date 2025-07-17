# Task 301: Create Master Integration Test

**Status:** Done

**Description:** Built a comprehensive integration test that runs the entire trace from a sample input file to a final output file.

**Key Changes:**
- Created `tests/integration` directory.
- Added `test_full_trace.py` with pytest fixtures for sample input data and a dummy `tasks.yml`.
- Refactored `atlas_cli/main.py` to accept `--input`, `--output`, and `--tasks_yml` arguments.
- Integrated `run_enrichment_trace` (from `enrich/main.py`) and `compute_and_merge_trust_scores` (from `trustforge/score.py`) into `atlas_cli/main.py`.
- Ensured `atlas_cli/main.py` orchestrates these functions based on the `tasks.yml`.
- Updated `test_full_trace.py` to assert on the creation and content of the output file.
- Corrected `sys.path` issues in `tests/integration/test_full_trace.py` and `atlas_cli/main.py` for proper module imports.

**Verification:**
- `pytest tests/integration/test_full_trace.py` executes successfully, confirming the end-to-end trace functionality.
