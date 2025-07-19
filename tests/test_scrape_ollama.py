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

