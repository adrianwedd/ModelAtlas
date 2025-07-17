import pytest

from atlas_schemas.config import Config


def test_config_missing_required_key(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(ValueError) as exc:
        Config()
    assert "LLM_API_KEY" in str(exc.value)


def test_config_initialization_with_key(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "dummy")
    cfg = Config()
    assert cfg.LLM_API_KEY == "dummy"
