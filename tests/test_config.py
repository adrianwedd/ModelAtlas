from pathlib import Path

import pytest

from atlas_schemas.config import Config


def test_config_initializes_without_env(monkeypatch, tmp_path):
    """Config must construct cleanly even with no env vars set."""
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    cfg = Config(_env_file=str(tmp_path / ".env.missing"))
    assert cfg.PROJECT_NAME == "ModelAtlas"
    assert cfg.LLM_API_KEY is None


def test_config_accepts_optional_llm_key(tmp_path):
    """LLM_API_KEY is optional; supplying it must not raise."""
    cfg = Config(LLM_API_KEY="sk-test", _env_file=str(tmp_path / ".env.missing"))
    assert cfg.LLM_API_KEY == "sk-test"
