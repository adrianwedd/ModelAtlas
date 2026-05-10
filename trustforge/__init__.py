"""Simple TrustForge scoring heuristics."""

from atlas_schemas.models import Model

LICENSE_SCORES = {
    "apache-2.0": 0.9,
    "mit": 0.9,
    "gpl-3.0": 0.6,
    "cc-by-nc": 0.4,
}

MAX_DOWNLOADS = 10_000_000


MAX_CONTEXT = 1_000_000  # 1M tokens as ceiling for normalisation


def compute_score(model: Model) -> float:
    """Compute a basic trust score for a model."""
    ann = model.annotations or {}

    license_key = (model.license or "").lower()
    license_score = LICENSE_SCORES.get(license_key, 0.5)

    downloads = model.pull_count if model.pull_count is not None else 0
    downloads_score = (
        min(downloads / MAX_DOWNLOADS, 1.0)
        if isinstance(downloads, (int, float))
        else 0.0
    )

    # OpenRouter-specific signals
    context_length = ann.get("context_length") or 0
    context_score = min(context_length / MAX_CONTEXT, 1.0) if context_length else 0.0

    is_free = ann.get("is_free")
    # Free models get a small bump (accessible); paid models with pricing data also non-zero
    pricing = ann.get("pricing") or {}
    has_pricing = any(v for v in pricing.values() if v)
    availability_score = 0.8 if is_free else (0.6 if has_pricing else 0.4)

    jailbreak_risk_score = ann.get("jailbreak_risk", 0.5)
    privacy_risk_score = ann.get("privacy_risk", 0.5)

    # Weight scheme: presence of structured metadata signals trustworthiness
    has_or_data = context_length > 0 or is_free is not None
    if has_or_data:
        score = (
            (0.35 * license_score)
            + (0.15 * downloads_score)
            + (0.20 * context_score)
            + (0.15 * availability_score)
            + (0.075 * jailbreak_risk_score)
            + (0.075 * privacy_risk_score)
        )
    else:
        score = (
            (0.50 * license_score)
            + (0.20 * downloads_score)
            + (0.15 * jailbreak_risk_score)
            + (0.15 * privacy_risk_score)
        )
    return round(max(0.0, min(score, 1.0)), 3)
