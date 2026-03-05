import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.enrich_metadata import enrich_model_metadata


def test_enrich_does_not_overwrite_existing_summary():
    model = {"name": "bert", "summary": "Already curated summary"}
    result = enrich_model_metadata(model)
    assert (
        result["summary"] == "Already curated summary"
    ), "enrich_model_metadata() must not overwrite non-empty existing fields"


def test_enrich_fills_missing_summary():
    model = {"name": "bert", "summary": ""}
    result = enrich_model_metadata(model)
    assert "summary" in result


def test_enrich_write_files_writes_model_data_not_just_enriched(tmp_path, monkeypatch):
    import tools.enrich_metadata as em

    monkeypatch.setattr(em, "ENRICHED_OUTPUTS_DIR", str(tmp_path / "enriched_outputs"))
    monkeypatch.setattr(em, "PROMPTS_DIR", str(tmp_path / "prompts"))
    monkeypatch.chdir(tmp_path)

    model = {"name": "bert", "description": "BERT model", "pull_count": 999}
    enrich_model_metadata(model, write_files=True)

    output = tmp_path / "enriched_outputs" / "bert_enriched.json"
    assert output.exists()
    written = json.loads(output.read_text())
    assert written.get("name") == "bert", "Written file must include full model data"
    assert written.get("pull_count") == 999, "Original model fields must be preserved"


def test_enrich_metadata_uses_settings_dirs():
    """enrich_metadata module-level constants must use settings, not hardcoded strings."""
    import tools.enrich_metadata as mod
    from atlas_schemas.config import settings

    assert (
        mod.MODELS_DIR == settings.MODELS_DIR
    ), f"MODELS_DIR must equal settings.MODELS_DIR ({settings.MODELS_DIR}), got {mod.MODELS_DIR!r}"
    assert str(mod.ENRICHED_OUTPUTS_DIR) == str(
        settings.ENRICHED_OUTPUTS_DIR
    ), f"ENRICHED_OUTPUTS_DIR must equal settings.ENRICHED_OUTPUTS_DIR, got {mod.ENRICHED_OUTPUTS_DIR!r}"
    assert str(mod.PROMPTS_DIR) == str(
        settings.PROMPTS_DIR
    ), f"PROMPTS_DIR must equal settings.PROMPTS_DIR, got {mod.PROMPTS_DIR!r}"


def test_main_does_not_overwrite_source_files(tmp_path, monkeypatch):
    import tools.enrich_metadata as em

    monkeypatch.setattr(em, "MODELS_DIR", str(tmp_path / "models"))
    monkeypatch.setattr(em, "ENRICHED_OUTPUTS_DIR", str(tmp_path / "enriched_outputs"))
    monkeypatch.setattr(em, "PROMPTS_DIR", str(tmp_path / "prompts"))

    models_dir = tmp_path / "models"
    models_dir.mkdir()
    source = models_dir / "bert.json"
    original_content = {"name": "bert", "description": "BERT", "pull_count": 1000}
    source.write_text(json.dumps(original_content))

    from tools.enrich_metadata import main

    main()

    read_back = json.loads(source.read_text())
    assert (
        read_back == original_content
    ), "main() must not overwrite the source model file"
