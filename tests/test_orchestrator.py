import asyncio
import json
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def test_enrich_node_no_collision_across_subdirs(tmp_path):
    """Two models with the same filename in different subdirs must produce distinct output files."""
    from enrich.orchestrator import enrich_node

    # Create two models with same filename in different subdirs
    hf_dir = tmp_path / "raw" / "huggingface"
    ol_dir = tmp_path / "raw" / "ollama"
    hf_dir.mkdir(parents=True)
    ol_dir.mkdir(parents=True)

    (hf_dir / "bert.json").write_text(json.dumps({"name": "bert-hf"}))
    (ol_dir / "bert.json").write_text(json.dumps({"name": "bert-ol"}))

    enriched_dir = tmp_path / "enriched"
    enriched_dir.mkdir()

    state = {
        "raw_models_dir": tmp_path / "raw",
        "enriched_models_dir": enriched_dir,
        "validated_models_dir": tmp_path / "validated",
        "final_output_file": tmp_path / "out.json",
    }

    with patch("enrich.orchestrator.enrich_model_metadata", side_effect=lambda d: d):
        enrich_node(state)

    output_files = list(enriched_dir.glob("*.json"))
    assert len(output_files) == 2, (
        f"Expected 2 outputs (no collision), got {len(output_files)}: "
        f"{[f.name for f in output_files]}"
    )


def test_orchestrator_has_no_main_block():
    """The orchestrator must not have a dead __main__ block."""
    src = (PROJECT_ROOT / "enrich" / "orchestrator.py").read_text()
    # The dead block starts with building an initial_state dict with hardcoded paths
    assert '"models/raw"' not in src, "Dead __main__ block still present"


def test_atlas_skip_scrape_uppercase_skips_scraping(tmp_path):
    """ATLAS_SKIP_SCRAPE=TRUE (uppercase) must also skip scraping."""
    from enrich.orchestrator import scrape_node

    state = {
        "raw_models_dir": tmp_path / "raw",
        "enriched_models_dir": tmp_path / "enriched",
        "validated_models_dir": tmp_path / "validated",
        "final_output_file": tmp_path / "out.json",
    }
    (tmp_path / "raw").mkdir()

    with patch.dict(os.environ, {"ATLAS_SKIP_SCRAPE": "TRUE"}):
        with patch("enrich.orchestrator.execute_hf_scraper") as mock_hf:
            with patch("enrich.orchestrator.scrape_ollama_models", new_callable=AsyncMock):
                asyncio.run(scrape_node(state))
                mock_hf.assert_not_called()


def test_atlas_skip_scrape_value_1_skips_scraping(tmp_path):
    """ATLAS_SKIP_SCRAPE=1 must also skip scraping."""
    from enrich.orchestrator import scrape_node

    state = {
        "raw_models_dir": tmp_path / "raw",
        "enriched_models_dir": tmp_path / "enriched",
        "validated_models_dir": tmp_path / "validated",
        "final_output_file": tmp_path / "out.json",
    }
    (tmp_path / "raw").mkdir()

    with patch.dict(os.environ, {"ATLAS_SKIP_SCRAPE": "1"}):
        with patch("enrich.orchestrator.execute_hf_scraper") as mock_hf:
            with patch("enrich.orchestrator.scrape_ollama_models", new_callable=AsyncMock):
                asyncio.run(scrape_node(state))
                mock_hf.assert_not_called()


def test_enrich_node_output_filename_matches_merge_enrichment_lookup(tmp_path):
    """Enrichment files must be named {model_name.replace('/','_')}_enriched.json
    so that merge_enrichment can find them by model name."""
    import json
    from unittest.mock import patch
    from enrich.orchestrator import enrich_node
    from atlas_schemas.data_io import merge_enrichment
    from atlas_schemas.models import Model

    hf_dir = tmp_path / "raw" / "huggingface"
    hf_dir.mkdir(parents=True)
    model_data = {"name": "google-bert/bert-base-uncased", "description": "BERT"}
    (hf_dir / "bert-base-uncased.json").write_text(json.dumps(model_data))

    enriched_dir = tmp_path / "enriched"
    enriched_dir.mkdir()

    state = {
        "raw_models_dir": tmp_path / "raw",
        "enriched_models_dir": enriched_dir,
        "validated_models_dir": tmp_path / "validated",
        "final_output_file": tmp_path / "out.json",
    }

    with patch("enrich.orchestrator.enrich_model_metadata", side_effect=lambda d: d):
        enrich_node(state)

    # merge_enrichment looks for "google-bert_bert-base-uncased_enriched.json"
    expected_slug = "google-bert_bert-base-uncased"
    expected_file = enriched_dir / f"{expected_slug}_enriched.json"
    assert expected_file.exists(), (
        f"Expected enrichment file {expected_file.name} not found. "
        f"Found: {[f.name for f in enriched_dir.glob('*.json')]}"
    )

    # Verify merge_enrichment can actually find and load it
    model = Model(name="google-bert/bert-base-uncased")
    merged = merge_enrichment(model, enriched_dir)
    assert merged.name == "google-bert/bert-base-uncased"
