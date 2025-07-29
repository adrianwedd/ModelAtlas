from pathlib import Path
from typing import Dict, List
import json

from atlas_schemas.models import Model

def load_model_from_json(path: Path) -> Model:
    """Load a Model instance from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return Model(**data)

def merge_enrichment(model: Model, enriched_outputs_dir: Path) -> Model:
    """Merge manual enrichment data into a Model instance."""
    name = model.name.replace("/", "_")
    enriched_path = enriched_outputs_dir / f"{name}_enriched.json"
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
