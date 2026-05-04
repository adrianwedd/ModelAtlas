"""Scrape OpenRouter API for the full model catalogue including free-tier models.

OpenRouter aggregates 200+ models from multiple providers under a single API.
Free models (pricing.prompt == "0" AND pricing.completion == "0") are especially
valuable as they can be used in benchmarks at zero cost.

Usage:
    python tools/scrape_openrouter.py
    python tools/scrape_openrouter.py --free-only
    python tools/scrape_openrouter.py --dry-run
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from atlas_schemas.config import settings  # noqa: E402
from common.logging import logger  # noqa: E402

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"
OPENROUTER_MODELS_DIR = settings.MODELS_DIR / "openrouter"


def fetch_openrouter_models(api_key: str | None = None) -> list[dict]:
    headers = {"HTTP-Referer": "https://modelatlas.ai"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(OPENROUTER_API_URL, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        logger.error("OpenRouter API error %s: %s", e.code, e.read(200).decode())
        return []
    except Exception as e:
        logger.error("Failed to fetch OpenRouter models: %s", e)
        return []

    models = data.get("data", [])
    logger.info("OpenRouter API returned %d models", len(models))
    return models


def is_free(model: dict) -> bool:
    pricing = model.get("pricing", {})
    return (
        str(pricing.get("prompt", "1")) == "0"
        and str(pricing.get("completion", "1")) == "0"
    )


def normalize_model(raw: dict) -> dict:
    pricing = raw.get("pricing", {})
    return {
        "name": raw.get("id", ""),
        "display_name": raw.get("name", ""),
        "source": "openrouter",
        "provider": raw.get("id", "").split("/")[0] if "/" in raw.get("id", "") else "",
        "context_length": raw.get("context_length"),
        "is_free": is_free(raw),
        "pricing": {
            "prompt_per_1m": pricing.get("prompt"),
            "completion_per_1m": pricing.get("completion"),
            "image_per_1m": pricing.get("image"),
            "request": pricing.get("request"),
        },
        "architecture": raw.get("architecture", {}),
        "top_provider": raw.get("top_provider", {}),
        "description": raw.get("description", ""),
        "created": raw.get("created"),
    }


def scrape_openrouter_models(
    free_only: bool = False, dry_run: bool = False
) -> list[dict]:
    api_key = settings.OPENROUTER_API_KEY
    raw_models = fetch_openrouter_models(api_key)
    if not raw_models:
        return []

    models = [normalize_model(m) for m in raw_models]
    if free_only:
        models = [m for m in models if m["is_free"]]
        logger.info("Filtered to %d free models", len(models))

    if dry_run:
        free_count = sum(1 for m in models if m["is_free"])
        logger.info(
            "Dry run — %d total, %d free. Skipping file writes.", len(models), free_count
        )
        for m in models:
            tag = " [FREE]" if m["is_free"] else ""
            logger.info("  %s%s", m["name"], tag)
        return models

    OPENROUTER_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for model in models:
        slug = model["name"].replace("/", "_").replace(":", "_")
        out_path = OPENROUTER_MODELS_DIR / f"{slug}.json"
        out_path.write_text(json.dumps(model, indent=2), encoding="utf-8")

    # Write split indices
    all_index = OPENROUTER_MODELS_DIR / "_index.json"
    all_index.write_text(json.dumps(models, indent=2), encoding="utf-8")

    free_models = [m for m in models if m["is_free"]]
    free_index = OPENROUTER_MODELS_DIR / "_free_index.json"
    free_index.write_text(json.dumps(free_models, indent=2), encoding="utf-8")

    logger.info(
        "OpenRouter scrape complete — %d total (%d free) saved to %s",
        len(models),
        len(free_models),
        OPENROUTER_MODELS_DIR,
    )
    return models


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--free-only", action="store_true", help="Only save free-tier models")
    parser.add_argument("--dry-run", action="store_true", help="Fetch but do not write files")
    args = parser.parse_args()
    result = scrape_openrouter_models(free_only=args.free_only, dry_run=args.dry_run)
    free = sum(1 for m in result if m["is_free"])
    print(f"Done: {len(result)} models ({free} free)")
