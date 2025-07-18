import os
import sys

# Ensure modules import correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from atlas_schemas.models import Model
from trustforge import compute_score

# Set dummy API keys to satisfy config initialization
os.environ.setdefault("LLM_API_KEY", "dummy")


def test_unknown_license_and_none_downloads():
    model = Model(name="test", license=None, pull_count=None)
    assert compute_score(model) == 0.35


def test_known_license_large_downloads():
    model = Model(name="test", license="MIT", pull_count=20_000_000)
    assert compute_score(model) == 0.93


def test_non_numeric_downloads():
    model = Model(name="test", license="apache-2.0", pull_count="1000")
    assert compute_score(model) == 0.63  # downloads_score treated as 0


def test_negative_downloads():
    model = Model(name="test", license="MIT", pull_count=-50_000_000)
    assert compute_score(model) == -0.87
