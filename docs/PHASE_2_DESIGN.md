# PHASE 2 DESIGN: Ollama Intelligence Enhancer

## ✳️ Scope
Augment scraped Ollama model metadata with deeper manifest decoding, human-readable tags, and quality scoring.

## ✅ Objectives
- [ ] Decode model capabilities from manifest blobs
- [ ] Store readable tag names with metadata
- [ ] Implement per-model data quality scoring

## Architecture Additions
- `decode_manifest_config(manifest)` in `utils/manifest_tools.py`
- Quality scoring logic in `utils/scoring.py`
- Modified tag parsing logic in `scraper/tags.py`

## Output Schema Additions
- `config`: full config.json fields (flattened)
- `tag`: human-readable tag string
- `quality_score`: completeness metrics

## ️ Roadmap
- [ ] Phase 2A: Implement core enrichers
- [ ] Phase 2B: Build enrichment-only postprocessor for legacy scrapes
- [ ] Phase 2C: Add README linker + lineage parsing
