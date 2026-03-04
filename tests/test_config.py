import pytest

from atlas_schemas.config import Config


def test_config_missing_required_key(monkeypatch, tmp_path):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    # Pass a nonexistent env_file so pydantic-settings does not read the .env on disk
    with pytest.raises(ValueError) as exc:
        Config(_env_file=str(tmp_path / ".env.nonexistent"))
    assert "LLM_API_KEY" in str(exc.value)


def test_config_initialization_with_key(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "dummy")
    cfg = Config()
    assert cfg.LLM_API_KEY == "dummy"
