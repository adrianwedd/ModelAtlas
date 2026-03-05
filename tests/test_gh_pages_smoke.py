"""
Playwright smoke test for the GH Pages catalog.
Starts a local http.server, loads the page, verifies key elements are rendered.

Run: pytest tests/test_gh_pages_smoke.py -v
Requires: pip install pytest-playwright && playwright install chromium
"""

import os
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PORT = 8877


@pytest.fixture(scope="module")
def http_server():
    """Serve site/ on localhost for the duration of the test module."""
    # Copy models_enriched.json into site/ if not already there
    src = ROOT / "models_enriched.json"
    dst = SITE / "models_enriched.json"
    if src.exists() and not dst.exists():
        import shutil

        shutil.copy(src, dst)

    proc = subprocess.Popen(
        ["python", "-m", "http.server", str(PORT), "--directory", str(SITE)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1)  # give server time to start
    yield f"http://localhost:{PORT}"
    proc.terminate()
    proc.wait()


@pytest.mark.playwright
def test_catalog_loads_and_shows_models(http_server, page):
    """Catalog page must load, fetch data, and show model table rows."""
    page.goto(http_server)

    # Wait for Alpine.js to populate the table
    page.wait_for_selector(".model-table tbody tr", timeout=10000)

    rows = page.locator(".model-table tbody tr").count()
    assert rows >= 100, f"Expected ≥100 model rows, got {rows}"


@pytest.mark.playwright
def test_search_filters_rows(http_server, page):
    """Typing in the search box must filter the visible rows."""
    page.goto(http_server)
    page.wait_for_selector(".model-table tbody tr", timeout=10000)

    total_before = page.locator(".model-table tbody tr").count()
    page.fill(".search-input", "bert")
    page.wait_for_timeout(300)  # debounce

    rows_after = page.locator(".model-table tbody tr").count()
    assert rows_after < total_before, "Search filter had no effect"
    assert rows_after >= 1, "Search for 'bert' should match at least one model"


@pytest.mark.playwright
def test_asr_column_shows_pending(http_server, page):
    """All ASR cells must show — (pending) since no benchmark data loaded yet."""
    page.goto(http_server)
    page.wait_for_selector(".asr-pending", timeout=10000)

    cells = page.locator(".asr-pending")
    count = cells.count()
    assert count >= 100, f"Expected ≥100 ASR pending cells, got {count}"
    # All should show em-dash
    first_text = cells.first.text_content().strip()
    assert first_text == "—", f"Expected '—', got {first_text!r}"
