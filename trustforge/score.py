"""Compute trust scores for model catalog."""

import glob
import json
import os
import sys
from pathlib import Path
from typing import List, Dict

sys.path.append(str(Path(__file__).resolve().parents[1]))
from trustforge import compute_score

MODELS_DIR = "models"
ENRICHED_OUTPUTS_DIR = "enriched_outputs"
OUTPUT_FILE = "models_enriched.json"


def load_model(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def merge_enrichment(model: Dict) -> Dict:
    name = model.get("name", "").replace("/", "_")
    enriched_path = os.path.join(ENRICHED_OUTPUTS_DIR, f"{name}_enriched.json")
    if os.path.exists(enriched_path):
        try:
            with open(enriched_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            model.update(data)
        except Exception:
            pass
    return model


def main() -> None:
    models: List[Dict] = []
    for path in glob.glob(os.path.join(MODELS_DIR, "*.json")):
        model = load_model(path)
        model = merge_enrichment(model)
        model["trust_score"] = compute_score(model)
        models.append(model)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(models, f, indent=2)


if __name__ == "__main__":
    main()
