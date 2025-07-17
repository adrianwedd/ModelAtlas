# Task 13: Integrate TrustForge in pipeline

## Summary
Implemented a simple TrustForge module and wired it into a new `enrich/main.py` pipeline script. The pipeline merges manual enrichment outputs with base model data and computes a trust score for each model. README and tasks.yml updated to reflect the integrated workflow.

## Notes
- Trust scores are based on license type and download counts using basic heuristics.
- The old standalone `trustforge/score.py` can still be executed directly, but running `python enrich/main.py` now performs all steps in one command.
