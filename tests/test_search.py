import os
import sys
from pathlib import Path

import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT_DIR)

from atlas_cli import search


def test_load_models_missing(tmp_path, capsys):
    path = tmp_path / "missing.json"
    models = search.load_models(path)
    captured = capsys.readouterr()
    assert models == []
    assert "Catalog not found" in captured.out


def test_search_models_basic():
    data = [
        {"name": "llama3", "summary": "great model"},
        {"name": "mistral", "summary": "fast model"},
        {"name": "tiny-llama", "summary": "small"},
    ]
    results = search.search_models("llama", data, top_k=2)
    assert [m["name"] for m in results] == ["llama3", "tiny-llama"]


def test_cli_outputs(monkeypatch):
    sample = [{"name": "llama3", "summary": "great"}]
    monkeypatch.setattr(search, "load_models", lambda catalog: sample)
    console = search.Console(record=True)
    monkeypatch.setattr(search, "console", console)
    search.cli("llama")
    output = console.export_text()
    assert "llama3" in output
