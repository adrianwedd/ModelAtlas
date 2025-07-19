# Task 101: Establish Single Source of Truth for Data Schemas

**Status:** Done

**Description:** Refactored the codebase to use a centralized set of Pydantic models for all data structures, eliminating hand-rolled dictionaries and making `schema.md` obsolete.

**Key Changes:**
- Created a new top-level `atlas_schemas` directory.
- Defined `TraceableItem` and `Model` Pydantic models in `atlas_schemas/models.py`.
- Updated `trustforge/__init__.py` to import and use the `Model` Pydantic model for `compute_score`.
- Modified `enrich/main.py` and `trustforge/score.py` to load JSON data into `Model` objects and use `.model_dump()` for serialization, replacing previous dictionary manipulations.
- Ensured `Optional` was imported in `atlas_schemas/config.py` to resolve `NameError`.

**Verification:**
- `enrich/main.py` and `trustforge/score.py` now execute successfully without Pydantic warnings.
- The codebase is now set up to enforce a unified data schema.
