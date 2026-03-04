import asyncio
import json
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "tools"))

# Ensure required config keys for tests
os.environ.setdefault("LLM_API_KEY", "dummy")
os.environ.setdefault("HUGGING_FACE_API_KEY", "dummy")
os.environ.setdefault("OPENAI_API_KEY", "dummy")

import scrape_ollama


@pytest.mark.asyncio
async def test_scrape_single_model(tmp_path):
    scrape_ollama.OLLAMA_MODELS_DIR = tmp_path / "models"
    scrape_ollama.DEBUG_DIR = tmp_path / "debug"
    scrape_ollama.LOG_FILE = tmp_path / "log.log"
    scrape_ollama.settings.MODELS_DIR = tmp_path
    scrape_ollama.settings.DEBUG_DIR = tmp_path / "debug"
    scrape_ollama.settings.LOG_FILE = tmp_path / "log.log"

    sample_detail = {"name": "foo", "page_hash": "abc", "description": "desc"}
    sample_tags = [{"tag": "latest"}]

    with patch("scrape_ollama.fetch_model_list", new=AsyncMock(return_value=["foo"])):
        with patch(
            "scrape_ollama.scrape_details", new=AsyncMock(return_value=sample_detail)
        ):
            with patch(
                "scrape_ollama.scrape_tags_page",
                new=AsyncMock(return_value=sample_tags),
            ):
                await scrape_ollama.scrape_ollama_models(concurrency=2)

    model_file = scrape_ollama.OLLAMA_MODELS_DIR / "foo.json"
    assert model_file.exists()
    data = json.loads(model_file.read_text(encoding="utf-8"))
    assert data["name"] == "foo"
    assert data["description"] == "desc"


@pytest.mark.asyncio
async def test_scrape_ollama_tolerates_one_failed_model(monkeypatch, tmp_path):
    """A single process_model exception must not abort the whole batch."""
    import httpx

    scrape_ollama.OLLAMA_MODELS_DIR = tmp_path / "models"
    scrape_ollama.DEBUG_DIR = tmp_path / "debug"
    scrape_ollama.LOG_FILE = tmp_path / "log.log"

    async def fake_fetch_model_list(client):
        return ["good-model", "bad-model"]

    call_count = [0]

    async def fake_process_model(client, name, semaphore):
        call_count[0] += 1
        if name == "bad-model":
            raise httpx.InvalidURL("bad url")
        return {"name": name, "tags": []}

    monkeypatch.setattr("scrape_ollama.fetch_model_list", fake_fetch_model_list)
    monkeypatch.setattr("scrape_ollama.process_model", fake_process_model)

    results = await scrape_ollama.scrape_ollama_models(concurrency=2)

    assert call_count[0] == 2  # both models were attempted
    assert len(results) == 1
    assert results[0]["name"] == "good-model"


@pytest.mark.asyncio
async def test_scrape_tags_page_href_tag_extraction(tmp_path):
    """scrape_tags_page must extract tag names from href, not get_text,
    to avoid digest hash concatenation (e.g. 'latest78fad5d182a7•')."""
    from unittest.mock import AsyncMock, patch
    import httpx

    html = """
    <html><body>
      <div class="group px-4 py-3">
        <a href="/library/phi4-mini:latest">latest<span class="font-mono">78fad5d182a7•</span></a>
        <p class="col-span-2">3.8 GB</p>
        <div class="flex text-neutral-500 text-xs items-center">
          <span class="font-mono">78fad5d182a7</span> · 2 weeks ago
        </div>
      </div>
      <div class="group px-4 py-3">
        <a href="/library/phi4-mini:3.8b">3.8b<span class="font-mono">1234abcd5678•</span></a>
        <p class="col-span-2">3.8 GB</p>
        <div class="flex text-neutral-500 text-xs items-center">
          <span class="font-mono">1234abcd5678</span> · 3 weeks ago
        </div>
      </div>
    </body></html>
    """

    async def fake_fetch(client, url):
        return html

    async def fake_fetch_manifest(client, model, tag="latest"):
        return None  # don't need manifest for this test

    with patch("scrape_ollama.fetch", new=AsyncMock(side_effect=fake_fetch)):
        with patch("scrape_ollama.fetch_manifest", new=AsyncMock(side_effect=fake_fetch_manifest)):
            import httpx
            async with httpx.AsyncClient() as client:
                tags = await scrape_ollama.scrape_tags_page(client, "phi4-mini")

    assert len(tags) == 2
    assert tags[0]["tag"] == "latest", f"Expected 'latest', got {tags[0]['tag']!r}"
    assert tags[1]["tag"] == "3.8b", f"Expected '3.8b', got {tags[1]['tag']!r}"


@pytest.mark.asyncio
async def test_scrape_ollama_does_not_add_duplicate_handlers(tmp_path):
    """Calling scrape_ollama_models twice must not add a second RotatingFileHandler."""
    import logging

    scrape_ollama.OLLAMA_MODELS_DIR = tmp_path / "models"
    scrape_ollama.DEBUG_DIR = tmp_path / "debug"
    scrape_ollama.LOG_FILE = tmp_path / "log.log"

    scrape_logger = logging.getLogger("ModelAtlas")
    sample_detail = {"name": "foo", "page_hash": "abc", "description": "desc"}
    sample_tags = [{"tag": "latest"}]

    with patch("scrape_ollama.fetch_model_list", new=AsyncMock(return_value=["foo"])):
        with patch("scrape_ollama.scrape_details", new=AsyncMock(return_value=sample_detail)):
            with patch("scrape_ollama.scrape_tags_page", new=AsyncMock(return_value=sample_tags)):
                await scrape_ollama.scrape_ollama_models(concurrency=1)
                count_after_first = len(scrape_logger.handlers)
                await scrape_ollama.scrape_ollama_models(concurrency=1)
                count_after_second = len(scrape_logger.handlers)

    assert count_after_second == count_after_first, (
        f"Handler count grew from {count_after_first} to {count_after_second} on second call"
    )
