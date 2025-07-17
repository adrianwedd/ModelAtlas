# Contributing to Ollama Intelligence Pipeline

## Getting Started
1. Fork the repository
2. Clone locally: `git clone https://github.com/youruser/ollama-pipeline.git`
3. Install dependencies: `pip install -r requirements.txt`
4. Install Playwright browsers: `playwright install`

## Development
- **Scraper**: `scrape_models.py`
- **Enrichment**: `enrich_models.py`
- **Visuals**: `generate_visuals.py`
- **README**: `generate_readme.py`

## Architecture & Style
- Follow PEP8 for Python
- Use Jinja2 for templating
- Ensure JSON schema compliance

## Pull Requests
- Write tests for new features
- Update `CHANGELOG.md`
- Tag maintainers for review

## Running Tests
Run `pytest` from the repository root. Ensure the dependencies in requirements.txt are installed and browsers are set up via `playwright install`.

