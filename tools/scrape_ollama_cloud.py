"""Scrape Ollama Cloud API for cloud-hosted model catalogue.

Unlike scrape_ollama.py (which scrapes ollama.com/library for locally-pullable
models), this scraper targets the authenticated Cloud API endpoint that lists
models available only on Ollama's GPU infrastructure — including frontier models
such as deepseek-v4-pro, glm-5.1, and kimi-k2:1t that are not pullable locally.

Usage:
    python tools/scrape_ollama_cloud.py
    python tools/scrape_ollama_cloud.py --dry-run
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

CLOUD_API_URL = "https://ollama.com/api/tags"
CLOUD_MODELS_DIR = settings.MODELS_DIR / "ollama_cloud"


def fetch_cloud_models(api_key: str) -> list[dict]:
    req = urllib.request.Request(
        CLOUD_API_URL,
        headers={"Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        logger.error("Ollama Cloud API error %s: %s", e.code, e.read(200).decode())
        return []
    except Exception as e:
        logger.error("Failed to fetch Ollama Cloud models: %s", e)
        return []

    models = data.get("models", [])
    logger.info("Ollama Cloud API returned %d models", len(models))
    return models


def normalize_model(raw: dict) -> dict:
    size_bytes = raw.get("size", 0)
    return {
        "name": raw["name"],
        "source": "ollama_cloud",
        "size_bytes": size_bytes,
        "size_gb": round(size_bytes / 1e9, 2) if size_bytes else None,
        "added_at": raw.get("modified_at", ""),
        "digest": raw.get("digest", ""),
        "details": raw.get("details", {}),
    }


def scrape_ollama_cloud_models(dry_run: bool = False) -> list[dict]:
    api_key = settings.OLLAMA_CLOUD_API_KEY
    if not api_key:
        logger.error(
            "OLLAMA_CLOUD_API_KEY not set. Add it to .env and re-run."
        )
        return []

    raw_models = fetch_cloud_models(api_key)
    if not raw_models:
        return []

    models = [normalize_model(m) for m in raw_models]

    if dry_run:
        logger.info("Dry run — skipping file writes. Models found:")
        for m in models:
            logger.info("  %s (%.1f GB)", m["name"], m.get("size_gb") or 0)
        return models

    CLOUD_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    saved = 0
    for model in models:
        slug = model["name"].replace(":", "_").replace("/", "_")
        out_path = CLOUD_MODELS_DIR / f"{slug}.json"
        out_path.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
        saved += 1

    # Write a combined index for downstream consumers
    index_path = CLOUD_MODELS_DIR / "_index.json"
    index_path.write_text(json.dumps(models, indent=2) + "\n", encoding="utf-8")

    logger.info(
        "Ollama Cloud scrape complete — %d models saved to %s", saved, CLOUD_MODELS_DIR
    )
    return models


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch but do not write files",
    )
    args = parser.parse_args()
    result = scrape_ollama_cloud_models(dry_run=args.dry_run)
    print(f"Done: {len(result)} cloud models")
