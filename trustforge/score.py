"""Compute trust scores for model catalog."""

import json
import sys
from pathlib import Path
from typing import List

sys.path.append(str(Path(__file__).resolve().parents[1]))
from atlas_schemas.data_io import load_model_from_json, merge_enrichment  # noqa: E402
from atlas_schemas.models import Model  # noqa: E402
from trustforge import compute_score  # noqa: E402


def compute_and_merge_trust_scores(
    input_dir: Path, output_file: Path, enriched_outputs_dir: Path
) -> None:
    models: List[Model] = []
    for path in Path(input_dir).rglob("*.json"):
        model = load_model_from_json(path)
        if model is None:
            continue
        model = merge_enrichment(model, enriched_outputs_dir)
        model.trust_score = compute_score(model)
        models.append(model)

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([model.model_dump() for model in models], f, indent=2)


# Removed if __name__ == "__main__" block
