"""Simple TrustForge scoring heuristics."""

from typing import Dict
from atlas_schemas.models import Model

LICENSE_SCORES = {
    "apache-2.0": 0.9,
    "mit": 0.9,
    "gpl-3.0": 0.6,
    "cc-by-nc": 0.4,
}

MAX_DOWNLOADS = 10_000_000

def compute_score(model: Model) -> float:
    """Compute a basic trust score for a model."""
    license_key = str(model.license).lower() if model.license else ""
    license_score = LICENSE_SCORES.get(license_key, 0.5)

    downloads = model.pull_count if model.pull_count is not None else 0
    downloads_score = min(downloads / MAX_DOWNLOADS, 1.0) if isinstance(downloads, (int, float)) else 0.0

    score = 0.7 * license_score + 0.3 * downloads_score
    return round(min(score, 1.0), 3)
