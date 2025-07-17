"""Simple enrichment pipeline that merges manual metadata and computes trust scores."""

import glob
import json
import os
import sys
from pathlib import Path
from typing import Dict, List

sys.path.append(str(Path(__file__).resolve().parents[1]))
from trustforge import compute_score

MODELS_DIR = "models"
ENRICHED_OUTPUTS_DIR = "enriched_outputs"
OUTPUT_FILE = "models_enriched.json"


def load_base_model(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_manual_enrichment(name: str) -> Dict:
    enriched_path = os.path.join(ENRICHED_OUTPUTS_DIR, f"{name}_enriched.json")
    if os.path.exists(enriched_path):
        try:
            with open(enriched_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def main() -> None:
    models: List[Dict] = []
    for path in glob.glob(os.path.join(MODELS_DIR, "*.json")):
        base = load_base_model(path)
        name_slug = base.get("name", "").replace("/", "_")
        enrichment = load_manual_enrichment(name_slug)
        base.update(enrichment)
        base["trust_score"] = compute_score(base)
        models.append(base)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(models, f, indent=2)


if __name__ == "__main__":
    main()
