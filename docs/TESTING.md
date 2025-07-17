# Testing Guide

This project uses **pytest** for all automated tests.

## Running the Test Suite

Install the Python dependencies and Playwright browsers first:

```bash
pip install -r requirements.txt
playwright install
```

Then execute the suite quietly with:

```bash
pytest -q
```

## Integration Test

A sample end-to-end trace test lives in `tests/integration/test_full_trace.py`.
Run it directly with:

```bash
pytest tests/integration/test_full_trace.py -q
```
