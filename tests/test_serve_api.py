import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


FAKE_MODELS = [
    {
        "name": "test-model",
        "similar_models": [{"name": "other-model", "score": 0.9}],
    }
]


@pytest.fixture
def client():
    with patch("tools.serve_api.load_models_data", return_value=FAKE_MODELS):
        import tools.serve_api as api_module
        from fastapi.testclient import TestClient
        yield TestClient(api_module.app)


def test_get_all_models(client):
    resp = client.get("/models")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_get_model_by_name_not_found(client):
    resp = client.get("/models/nonexistent")
    assert resp.status_code == 404


def test_get_similar_models_not_found(client):
    resp = client.get("/models/nonexistent/similar")
    assert resp.status_code == 404


def test_no_duplicate_similar_route():
    """Each route path must appear only once."""
    import tools.serve_api as api_module
    similar_routes = [
        r for r in api_module.app.routes
        if hasattr(r, "path") and str(r.path).endswith("/similar")
    ]
    assert len(similar_routes) == 1, (
        f"Expected 1 /similar route, got {len(similar_routes)}: "
        f"{[r.path for r in similar_routes]}"
    )


def test_load_models_data_returns_empty_on_nonexistent_file(tmp_path):
    """load_models_data must return [] if data file doesn't exist."""
    import tools.serve_api as api
    original = api.MODELS_DATA_PATH
    api.MODELS_DATA_PATH = tmp_path / "nonexistent.json"
    try:
        result = api.load_models_data()
        assert result == []
    finally:
        api.MODELS_DATA_PATH = original


def test_load_models_data_returns_empty_on_corrupted_json(tmp_path):
    """load_models_data must return [] on corrupted JSON, not raise."""
    import tools.serve_api as api
    bad = tmp_path / "bad.json"
    bad.write_text("{corrupted")
    original = api.MODELS_DATA_PATH
    api.MODELS_DATA_PATH = bad
    try:
        result = api.load_models_data()
        assert result == []
    finally:
        api.MODELS_DATA_PATH = original


def test_get_all_models_reflects_file_changes(tmp_path):
    """get_all_models must load fresh data on each call, not use cached global."""
    import json as json_mod
    import tools.serve_api as api
    from fastapi.testclient import TestClient

    data_file = tmp_path / "models.json"
    data_file.write_text(json_mod.dumps([{"name": "bert"}]))

    original = api.MODELS_DATA_PATH
    api.MODELS_DATA_PATH = data_file
    try:
        client = TestClient(api.app)
        resp1 = client.get("/models")
        assert len(resp1.json()) == 1

        # Simulate file update between requests
        data_file.write_text(json_mod.dumps([{"name": "bert"}, {"name": "gpt2"}]))
        resp2 = client.get("/models")
        assert len(resp2.json()) == 2, "API must reflect updated file on second request"
    finally:
        api.MODELS_DATA_PATH = original
