import json
from pathlib import Path
from typing import List, Dict, Any
from pydantic import ValidationError

from atlas_schemas.models import Model

def normalize_license(license_str: str) -> str:
    if not license_str:
        return ""
    license_str = license_str.lower().strip()
    if "mit" in license_str:
        return "MIT"
    # Add more license normalization rules as needed
    return license_str

def normalize_architecture(arch_str: str) -> str:
    if not arch_str:
        return ""
    arch_str = arch_str.lower().strip()
    if "transformer" in arch_str:
        return "Transformer"
    # Add more architecture normalization rules as needed
    return arch_str

def deduplicate_tags(tags: List[str]) -> List[str]:
    return sorted(list(set([tag.strip() for tag in tags if tag.strip()])))

def validate_and_normalize_models(input_path: Path, output_path: Path) -> None:
    if not input_path.exists():
        print(f"Error: Input file not found at {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        models_data = json.load(f)

    validated_models = []
    for model_data in models_data:
        # Apply normalization
        if "license" in model_data:
            model_data["license"] = normalize_license(model_data["license"])
        if "architecture" in model_data:
            model_data["architecture"] = normalize_architecture(model_data["architecture"])
        if "tags" in model_data and isinstance(model_data["tags"], list):
            model_data["tags"] = deduplicate_tags(model_data["tags"])

        try:
            # Validate against schema
            validated_model = Model(**model_data)
            validated_models.append(validated_model.model_dump())
        except ValidationError as e:
            print(f"Validation Error for model {model_data.get('name', 'Unknown')}: {e}")
            # Optionally, handle invalid models (e.g., skip, log, or store separately)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(validated_models, f, indent=2)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Normalize and validate enriched model metadata.")
    parser.add_argument("--input", type=Path, default=Path("data/models_enriched.json"),
                        help="Path to the input JSON file containing enriched models.")
    parser.add_argument("--output", type=Path, default=Path("data/models_validated.json"),
                        help="Path to the output JSON file for validated models.")
    args = parser.parse_args()

    validate_and_normalize_models(args.input, args.output)
