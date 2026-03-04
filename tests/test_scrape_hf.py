import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.scrape_hf import parse_pull_count


def test_parse_pull_count_handles_garbage():
    assert parse_pull_count("not-a-number") == 0


def test_parse_pull_count_handles_millions():
    assert parse_pull_count("1.2M") == 1_200_000


def test_parse_pull_count_handles_thousands():
    assert parse_pull_count("650K") == 650_000


def test_parse_pull_count_handles_int():
    assert parse_pull_count(42) == 42


def test_parse_pull_count_handles_empty():
    assert parse_pull_count("") == 0
    assert parse_pull_count(None) == 0


def test_scrape_hf_uses_settings_models_dir():
    """execute_hf_scraper must derive output dir from settings.MODELS_DIR, not hardcode 'models'."""
    import inspect
    import tools.scrape_hf as hf_module
    src = inspect.getsource(hf_module.execute_hf_scraper)
    assert 'os.path.join("models"' not in src, (
        "execute_hf_scraper must not hardcode the string 'models' — use settings.MODELS_DIR"
    )
