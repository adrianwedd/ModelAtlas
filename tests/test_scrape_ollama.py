import asyncio
import json
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, 'tools'))

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
        with patch("scrape_ollama.scrape_details", new=AsyncMock(return_value=sample_detail)):
            with patch("scrape_ollama.scrape_tags_page", new=AsyncMock(return_value=sample_tags)):
                await scrape_ollama.scrape_ollama_models(concurrency=2)

    model_file = scrape_ollama.OLLAMA_MODELS_DIR / "foo.json"
    assert model_file.exists()
    data = json.loads(model_file.read_text(encoding="utf-8"))
    assert data["name"] == "foo"
    assert data["description"] == "desc"

    assert scrape_ollama.LOG_FILE.exists()
    log_content = scrape_ollama.LOG_FILE.read_text(encoding="utf-8")
    assert "Processing Ollama.com model: foo" in log_content


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
