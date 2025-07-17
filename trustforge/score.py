"""Compute trust scores for model catalog."""

import glob
import json
import os
import sys
from pathlib import Path
from typing import List, Dict

sys.path.append(str(Path(__file__).resolve().parents[1]))
from trustforge import compute_score
from atlas_schemas.models import Model
from atlas_schemas.config import settings



def load_model(path: str) -> Model:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return Model(**data)


def merge_enrichment(model: Model) -> Model:
    name = model.name.replace("/", "_")
    enriched_path = settings.ENRICHED_OUTPUTS_DIR / f"{name}_enriched.json"
    if enriched_path.exists():
        try:
            with open(enriched_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            model_dict = model.model_dump()
            model_dict.update(data)
            return Model(**model_dict)
        except Exception:
            pass
    return model


def main() -> None:
    models: List[Model] = []
    for path in glob.glob(str(settings.MODELS_DIR / "*.json")):
        model = load_model(path)
        model = merge_enrichment(model)
        model.trust_score = compute_score(model)
        models.append(model)

    with open(settings.PROJECT_ROOT / settings.OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump([model.model_dump() for model in models], f, indent=2)


if __name__ == "__main__":
    main()
