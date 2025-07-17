import argparse
import sys
import json
import yaml
from pathlib import Path

# Add the project root to sys.path to enable imports from atlas_schemas
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from common.logging import logger

from atlas_schemas.config import settings
from enrich.main import run_enrichment_trace
from trustforge.score import compute_and_merge_trust_scores

def main():
    parser = argparse.ArgumentParser(description="ModelAtlas CLI")
    parser.add_argument("--input", type=str, help="Input file path")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--tasks_yml", type=str, help="Tasks YAML file path")

    args = parser.parse_args()

    logger.info("Input: %s", args.input)
    logger.info("Output: %s", args.output)
    logger.info("Tasks YML: %s", args.tasks_yml)

    # Load tasks from tasks.yml
    tasks_file_path = Path(args.tasks_yml) if args.tasks_yml else PROJECT_ROOT / "tasks.yml"
    if not tasks_file_path.exists():
        logger.error("tasks.yml not found at %s", tasks_file_path)
        sys.exit(1)

    with open(tasks_file_path, "r") as f:
        tasks = yaml.safe_load(f)

    # Convert input/output paths to Path objects
    input_path = Path(args.input) if args.input else settings.MODELS_DIR
    output_path = Path(args.output) if args.output else (settings.PROJECT_ROOT / settings.OUTPUT_FILE)

    # Simple orchestration based on task IDs (this will be expanded)
    for task in tasks:
        if task["id"] == 2: # Enrich model metadata with LLM (now run_enrichment_trace)
            logger.info("Executing Task %s: %s", task["id"], task["title"])
            run_enrichment_trace(
                input_dir=input_path,
                output_file=output_path,
                enriched_outputs_dir=settings.ENRICHED_OUTPUTS_DIR
            )
        elif task["id"] == 10: # Evaluate and rank models by trust and transparency (now compute_and_merge_trust_scores)
            logger.info("Executing Task %s: %s", task["id"], task["title"])
            compute_and_merge_trust_scores(
                input_dir=input_path, # Assuming models are in MODELS_DIR
                output_file=output_path, # Overwriting for simplicity
                enriched_outputs_dir=settings.ENRICHED_OUTPUTS_DIR
            )

    logger.info("Trace execution complete.")

if __name__ == "__main__":
    main()