# Contributing to ModelAtlas

## Getting Started
1. Fork the repository
2. Clone locally: `git clone https://github.com/youruser/ModelAtlas.git`
3. Install dependencies: `pip install -r requirements.txt` (includes packages like `playwright`, `beautifulsoup4`, and `requests` used by the test suite)
4. Install Playwright browsers: `playwright install`
5. Optionally run `make test-deps` to perform both steps at once

## Development
- **Scraper**: `python tools/scrape_*.py`
- **Enrichment**: `python enrich/main.py`
- **Visuals**: `generate_visuals.py`
- **README**: `generate_readme.py`

## Terminology Lexicon
To maintain consistency and clarity across the project, please adhere to the following terminology:

- **Trace**: The canonical term for a single, end-to-end execution of the trace, from data ingestion to final output. This replaces terms like 'job', 'run', 'workflow', or 'pipeline' when referring to a complete execution.

## Architecture & Style
- Follow PEP8 for Python
- Use Jinja2 for templating
- Ensure JSON schema compliance

## Pull Requests
- Write tests for new features
- Tag maintainers for review
- Use the provided pull request template

## Issues
Please open bug reports and feature requests using the templates in `.github/ISSUE_TEMPLATE/`.

## Running Tests
Run `pytest` from the repository root. Ensure the dependencies in requirements.txt are installed and browsers are set up via `playwright install`.

