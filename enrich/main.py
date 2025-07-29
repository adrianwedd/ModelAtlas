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
from atlas_schemas.data_io import load_model_from_json, merge_enrichment


def run_enrichment_trace(input_dir: Path, output_file: Path, enriched_outputs_dir: Path) -> None:
    models: List[Model] = []
    for path in glob.glob(str(input_dir / "*.json")):
        base = load_model_from_json(Path(path))
        updated_model = merge_enrichment(base, enriched_outputs_dir)
        updated_model.trust_score = compute_score(updated_model)
        models.append(updated_model)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([model.model_dump() for model in models], f, indent=2)

# Removed if __name__ == "__main__" block