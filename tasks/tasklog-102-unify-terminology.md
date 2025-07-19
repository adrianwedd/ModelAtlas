# Task 102: Unify Project Terminology

**Status:** Done

**Description:** Decided on and enforced 'Trace' as the single, canonical term for a pipeline execution across the entire repository (code, docs, CLI).

**Key Changes:**
- Updated `CONTRIBUTING.md` to include a terminology lexicon, defining 'Trace' as the official term.
- Replaced instances of 'job', 'run', 'workflow', and 'pipeline' with 'trace' in relevant files, carefully avoiding literal commands or scraped content.
- Modified docstrings, comments, and descriptions to reflect the new terminology.
- Renamed `PipelineConfig` to `TraceConfig` in `atlas_schemas/models.py` and updated its usage.

**Verification:**
- Manual inspection of changed files confirms consistent terminology.
- Codebase remains functional after replacements.
