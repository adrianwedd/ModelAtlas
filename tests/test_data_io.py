import json
from unittest.mock import patch

import pytest

from atlas_schemas.data_io import load_model_from_json, merge_enrichment
from atlas_schemas.models import Model


@pytest.fixture
def base_model():
    return Model(name="test-model")


def test_merge_enrichment_logs_on_bad_json(base_model, tmp_path):
    """merge_enrichment must log an error and return base model on bad JSON."""
    bad_file = tmp_path / "test-model_enriched.json"
    bad_file.write_text("{invalid json}")

    with patch("atlas_schemas.data_io.logger") as mock_log:
        result = merge_enrichment(base_model, tmp_path)

    mock_log.error.assert_called_once()
    assert result.name == "test-model"


def test_merge_enrichment_returns_unchanged_when_no_file(base_model, tmp_path):
    """No enriched file → return base model unchanged, no exception."""
    result = merge_enrichment(base_model, tmp_path)
    assert result.name == "test-model"


def test_merge_enrichment_applies_valid_enrichment(base_model, tmp_path):
    """Valid enriched JSON → fields merged into returned model."""
    enriched = tmp_path / "test-model_enriched.json"
    enriched.write_text(json.dumps({"summary": "great model"}))

    result = merge_enrichment(base_model, tmp_path)
    assert result.summary == "great model"


def test_load_model_from_json_returns_none_on_missing_file(tmp_path):
    result = load_model_from_json(tmp_path / "nonexistent.json")
    assert result is None


def test_load_model_from_json_returns_none_on_bad_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json}")
    result = load_model_from_json(bad)
    assert result is None


def test_load_model_from_json_returns_model_on_valid_file(tmp_path):
    good = tmp_path / "model.json"
    good.write_text('{"name": "test-model"}')
    result = load_model_from_json(good)
    assert result is not None
    assert result.name == "test-model"
