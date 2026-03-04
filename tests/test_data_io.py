import json
import pytest
from pathlib import Path
from unittest.mock import patch
from atlas_schemas.data_io import merge_enrichment
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
