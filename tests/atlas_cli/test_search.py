import pytest
from pathlib import Path
import json
from unittest.mock import patch, MagicMock

from atlas_cli.search import load_models, search_models, display_results, cli

@pytest.fixture
def mock_catalog_path(tmp_path):
    # Create a temporary directory and a dummy catalog file
    catalog_dir = tmp_path / "data"
    catalog_dir.mkdir()
    catalog_file = catalog_dir / "models_enriched.json"
    dummy_data = [
        {"name": "Llama 2", "summary": "A large language model from Meta"},
        {"name": "Gemma", "summary": "A lightweight, state-of-the-art open model from Google"},
        {"name": "Mistral", "summary": "A powerful language model"},
        {"name": "Code Llama", "summary": "Llama for code generation"},
    ]
    with open(catalog_file, "w") as f:
        json.dump(dummy_data, f)
    return catalog_file

def test_load_models_success(mock_catalog_path):
    models = load_models(mock_catalog_path)
    assert len(models) == 4
    assert models[0]["name"] == "Llama 2"

def test_load_models_file_not_found(tmp_path):
    non_existent_path = tmp_path / "non_existent.json"
    with patch("atlas_cli.search.console.print") as mock_print:
        models = load_models(non_existent_path)
        assert models == []
        mock_print.assert_called_with(f"[bold red]Catalog not found at {non_existent_path}.[/]")

def test_search_models_basic_query():
    models = [
        {"name": "Llama 2", "summary": "A large language model from Meta"},
        {"name": "Gemma", "summary": "A lightweight, state-of-the-art open model from Google"},
    ]
    results = search_models("llama", models)
    assert len(results) == 1
    assert results[0]["name"] == "Llama 2"

def test_search_models_multiple_matches():
    models = [
        {"name": "Llama 2", "summary": "A large language model from Meta"},
        {"name": "Code Llama", "summary": "Llama for code generation"},
        {"name": "Mistral", "summary": "A powerful language model"},
    ]
    results = search_models("llama", models)
    assert len(results) == 2
    result_names = [m["name"] for m in results]
    assert "Llama 2" in result_names
    assert "Code Llama" in result_names

def test_search_models_no_match():
    models = [
        {"name": "Llama 2", "summary": "A large language model from Meta"},
    ]
    results = search_models("nonexistent", models)
    assert results == []

def test_search_models_top_k():
    models = [
        {"name": "Model A", "summary": "summary A A A"},
        {"name": "Model B", "summary": "summary B B"},
        {"name": "Model C", "summary": "summary C"},
    ]
    results = search_models("summary", models, top_k=2)
    assert len(results) == 2
    assert results[0]["name"] == "Model A"
    assert results[1]["name"] == "Model B"

@patch("atlas_cli.search.console.print")
def test_display_results(mock_print):
    models = [
        {"name": "Test Model", "summary": "This is a test summary"},
    ]
    display_results(models)
    mock_print.assert_called_once()
    # Further assertions could check the content of the printed table if needed

@patch("atlas_cli.search.load_models")
@patch("atlas_cli.search.search_models")
@patch("atlas_cli.search.display_results")
@patch("atlas_cli.search.console.print")
def test_cli_with_results(mock_console_print, mock_display_results, mock_search_models, mock_load_models, mock_catalog_path):
    mock_load_models.return_value = [{"name": "Model1", "summary": "Summary1"}]
    mock_search_models.return_value = [{"name": "Model1", "summary": "Summary1"}]
    cli("test_query", catalog=mock_catalog_path)
    mock_load_models.assert_called_once_with(mock_catalog_path)
    mock_search_models.assert_called_once_with("test_query", [{"name": "Model1", "summary": "Summary1"}], top_k=5)
    mock_display_results.assert_called_once_with([{"name": "Model1", "summary": "Summary1"}])
    mock_console_print.assert_not_called() # Should not print "No matches found."

@patch("atlas_cli.search.load_models")
@patch("atlas_cli.search.search_models")
@patch("atlas_cli.search.console.print")
def test_cli_no_results(mock_console_print, mock_search_models, mock_load_models, mock_catalog_path):
    mock_load_models.return_value = [{"name": "Model1", "summary": "Summary1"}]
    mock_search_models.return_value = []
    cli("test_query", catalog=mock_catalog_path)
    mock_console_print.assert_called_once_with("[bold yellow]No matches found.[/]")
