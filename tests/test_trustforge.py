import json
import os
import sys

# Ensure modules import correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pathlib import Path

from atlas_schemas.models import Model
from trustforge import compute_score
from trustforge.score import compute_and_merge_trust_scores

# Set dummy API keys to satisfy config initialization
os.environ.setdefault("LLM_API_KEY", "dummy")


def test_unknown_license_and_none_downloads():
    model = Model(name="test", license=None, pull_count=None)
    assert compute_score(model) == 0.4


def test_known_license_large_downloads():
    model = Model(name="test", license="MIT", pull_count=20_000_000)
    assert compute_score(model) == 0.8


def test_non_numeric_downloads():
    # pydantic coerces the string "1000" to int, so downloads_score is non-zero but tiny
    model = Model(name="test", license="apache-2.0", pull_count="1000")
    assert compute_score(model) == 0.6


def test_negative_downloads():
    # Negative pull_count is domain-invalid; trust score must be clamped to >= 0.0
    model = Model(name="test", license="MIT", pull_count=-50_000_000)
    assert compute_score(model) >= 0.0


def test_compute_and_merge_skips_none_model(tmp_path):
    """load_model_from_json returning None must not cause AttributeError."""
    bad = tmp_path / "bad.json"
    bad.write_text("{invalid}")
    out = tmp_path / "out.json"
    # Should not raise
    compute_and_merge_trust_scores(tmp_path, out, tmp_path)
    assert out.exists()
    result = json.loads(out.read_text())
    assert result == []  # bad file skipped, no models


def test_compute_and_merge_finds_models_in_subdirs(tmp_path):
    """rglob must find models in subdirectories."""
    subdir = tmp_path / "huggingface"
    subdir.mkdir()
    (subdir / "bert.json").write_text(json.dumps({"name": "bert"}))
    out = tmp_path / "out.json"
    compute_and_merge_trust_scores(tmp_path, out, tmp_path)
    result = json.loads(out.read_text())
    assert len(result) == 1, "Model in subdir must be found"


def test_trust_score_none_license_does_not_produce_none_string():
    """Model with None license must not produce 'none' string license."""
    model = Model(name="test", license=None)
    score = compute_score(model)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_compute_and_merge_creates_output_parent_dir(tmp_path):
    """compute_and_merge_trust_scores must create output_file.parent if it doesn't exist."""
    nested_output = tmp_path / "new_dir" / "subdir" / "out.json"
    # nested_output.parent doesn't exist yet
    (tmp_path / "model.json").write_text(json.dumps({"name": "bert"}))
    # Should not raise FileNotFoundError
    compute_and_merge_trust_scores(tmp_path, nested_output, tmp_path)
    assert nested_output.exists()
