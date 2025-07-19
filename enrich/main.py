"""Simple enrichment trace that merges manual metadata and computes trust scores."""

import glob
import json
import os
import sys
from pathlib import Path
from typing import Dict, List

sys.path.append(str(Path(__file__).resolve().parents[1]))
from trustforge import compute_score
from atlas_schemas.models import Model
from atlas_schemas.config import settings


def load_base_model(path: str) -> Model:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return Model(**data)

def load_manual_enrichment(name: str, enriched_outputs_dir: Path) -> Dict:
    enriched_path = enriched_outputs_dir / f"{name}_enriched.json"
    if enriched_path.exists():
        try:
            with open(enriched_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def run_enrichment_trace(input_dir: Path, output_file: Path, enriched_outputs_dir: Path) -> None:
    models: List[Model] = []
    for path in glob.glob(str(input_dir / "*.json")):
        base = load_base_model(path)
        name_slug = base.name.replace("/", "_")
        enrichment = load_manual_enrichment(name_slug, enriched_outputs_dir)
        base_dict = base.model_dump() # Convert to dict for update
        base_dict.update(enrichment)
        updated_model = Model(**base_dict) # Re-instantiate Model with updated data
        updated_model.trust_score = compute_score(updated_model)
        models.append(updated_model)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([model.model_dump() for model in models], f, indent=2)

# Removed if __name__ == "__main__" block