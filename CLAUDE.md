# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Setup and Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers for web scraping
playwright install

# Install test dependencies
make test-deps
```

### Running the System
```bash
# Run enrichment trace (main entry point)
python enrich/main.py

# Run scrapers individually
python tools/scrape_hf.py      # Hugging Face scraper
python tools/scrape_ollama.py  # Ollama scraper

# Use the CLI interface
python atlas_cli/main.py --input data/models --output models_enriched.json

# Generate documentation
make -C docs html
```

### Testing
```bash
# Run all tests
pytest

# Run integration tests specifically
pytest tests/integration/

# Run specific test file
pytest tests/test_scrape_ollama.py
```

## Architecture Overview

ModelAtlas is a forensic-grade AI model metadata enrichment system with the following key components:

### Core Components
- **atlas_cli/**: CLI interface that orchestrates the enrichment trace
- **enrich/**: Main enrichment trace logic that merges metadata and computes scores
- **trustforge/**: Trust scoring engine using heuristic fusion
- **atlas_schemas/**: Centralized Pydantic models for data structures and configuration
- **tools/**: Individual scraper scripts for Hugging Face and Ollama

### Data Flow Architecture
1. **Data Ingestion**: Scrapers collect raw model metadata from Hugging Face and Ollama
2. **Enrichment**: Manual enrichments are loaded from `enriched_outputs/` directory
3. **Trust Scoring**: TrustForge computes trust scores based on multiple heuristics
4. **Output**: Final enriched models are written to JSON format

### Key Data Structures
- `Model`: Main Pydantic model representing AI models with metadata
- `TraceableItem`: Base class for items flowing through the enrichment trace
- `TraceConfig`: Configuration for trace execution

### Configuration Management
- Uses centralized `atlas_schemas/config.py` with Pydantic settings
- Configuration loaded from `.env` file with sane defaults
- Settings accessible via `from atlas_schemas.config import settings`

## Development Workflow

### Terminology
- **Trace**: The canonical term for end-to-end execution (not "job", "run", "workflow", or "pipeline")
- Follow the terminology lexicon in `CONTRIBUTING.md`

### Task Management
- Tasks are defined in `tasks.yml` with priorities, dependencies, and status
- Task logs are maintained in `tasks/tasklog-{task_id}-{slug}.md`
- Use the execution protocols defined in `AGENTS.md`

### Data Storage
- Raw scraped data: `models/huggingface/` and `models/ollama/`
- Manual enrichments: `enriched_outputs/`
- Final output: `models_enriched.json`
- Uses Git LFS for large JSON files

### File Locations
- Main enrichment logic: `enrich/main.py:31` (`run_enrichment_trace`)
- Trust scoring: `trustforge/score.py:38` (`compute_and_merge_trust_scores`)
- CLI orchestration: `atlas_cli/main.py:15` (`main`)
- Data models: `atlas_schemas/models.py`

## Important Implementation Notes

### HTTP Caching
- All scrapers use `requests-cache` with SQLite backend (`.cache/http.sqlite`)
- Use `--no-cache` flag to disable caching during development

### Error Handling
- Scrapers log to dedicated files (`ollama_scraper.log`, `hf_scraper.log`)
- Enrichment errors are logged to `enrichment.log`
- Use UTF-8 encoding for all file operations

### Schema Validation
- All data structures use Pydantic models from `atlas_schemas`
- Manual enrichments must be compatible with the `Model` schema
- Validation happens automatically when creating `Model` instances

### Testing Strategy
- Integration test in `tests/integration/test_full_trace.py` runs end-to-end trace
- Unit tests cover individual scrapers and core logic
- Use pytest for all testing

## Development Tips

- The system expects manual enrichment files in format `{model_name_slug}_enriched.json`
- Model names with "/" are converted to "_" for file naming
- Trust scores are computed automatically during enrichment
- All HTTP requests are cached by default to speed up development