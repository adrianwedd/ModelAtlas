import json
from pathlib import Path

import pytest

try:
    import jsonschema
except ImportError:  # pragma: no cover - install in CI
    jsonschema = None


@pytest.mark.skipif(jsonschema is None, reason="jsonschema package not available")
def test_models_validate_against_schema():
    repo_root = Path(__file__).resolve().parents[1]
    data_file = repo_root / "data" / "models_validated.json"
    schema_file = repo_root / "schemas" / "model.schema.json"

    if not data_file.exists():
        pytest.skip(f"{data_file} not present")
    if not schema_file.exists():
        pytest.skip("schema file missing")

    data = json.loads(data_file.read_text(encoding="utf-8"))
    schema = json.loads(schema_file.read_text(encoding="utf-8"))

    assert isinstance(data, list), "validated models should be a list"
    for entry in data:
        jsonschema.validate(entry, schema)
