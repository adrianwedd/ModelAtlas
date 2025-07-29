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

    # Placeholder for Jailbreak Risk and Privacy Risk from RISK_HEURISTICS.md
    # Assuming model.metadata might contain these scores or related flags
    jailbreak_risk_score = model.metadata.get("jailbreak_risk", 0.5) # Example: 0.0 (high) to 1.0 (low)
    privacy_risk_score = model.metadata.get("privacy_risk", 0.5) # Example: 0.0 (high) to 1.0 (low)

    # Combine scores with arbitrary weights
    score = (0.5 * license_score) + (0.2 * downloads_score) + (0.15 * jailbreak_risk_score) + (0.15 * privacy_risk_score)
    return round(min(score, 1.0), 3)
