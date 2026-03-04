"""Script to generate enrichment prompts and placeholders for AI model metadata."""

import json
import os
import time

from atlas_schemas.config import settings
from common.logging import logger

LOG_FILE = settings.LOG_FILE
MODELS_DIR = "models"
PROMPTS_DIR = "enrichment_prompts"
ENRICHED_OUTPUTS_DIR = "enriched_outputs"


def simulate_llm_enrichment(prompt: str, model_name: str) -> dict:
    """Placeholder: returns empty enrichment structure until LLM is wired in."""
    return {
        "summary": "",
        "use_cases": [],
        "strengths": [],
        "weaknesses": [],
        "meta": {
            "rated_by": "placeholder",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
    }


def enrich_model_metadata(model_data: dict) -> dict:
    """Generates prompts for subjective enrichment and writes output files."""
    model_name = model_data.get("name", "unknown_model").replace("/", "_")

    prompt_filename = os.path.join(PROMPTS_DIR, f"{model_name}_prompt.txt")
    enriched_output_filename = os.path.join(
        ENRICHED_OUTPUTS_DIR, f"{model_name}_enriched.json"
    )

    description = model_data.get("description", "No description available.")

    # Build prompt without embedding triple-quotes inside the f-string
    prompt_lines = [
        "You are an elite AI analyst.",
        "",
        "Model: " + model_data.get("name", "unknown"),
        "",
        "Raw description:",
        "---",
        description,
        "---",
        "",
        "Return a JSON object with: summary, use_cases, strengths, weaknesses.",
    ]
    prompt_content = "\n".join(prompt_lines)

    with open(prompt_filename, "w", encoding="utf-8") as f:
        f.write(prompt_content)
    logger.info("Generated enrichment prompt: %s", prompt_filename)

    enriched_data = simulate_llm_enrichment(prompt_content, model_name)

    with open(enriched_output_filename, "w", encoding="utf-8") as f:
        json.dump(enriched_data, f, indent=2)
    logger.info("Created enrichment output: %s", enriched_output_filename)

    model_data["enrichment_prompt_path"] = prompt_filename
    model_data["manual_enriched_output_path"] = enriched_output_filename

    return model_data


def main():
    logger.info("Starting model enrichment process.")

    try:
        os.makedirs(PROMPTS_DIR, exist_ok=True)
    except Exception as e:
        logger.error("Failed to create prompts directory %s: %s", PROMPTS_DIR, e)
        return

    try:
        os.makedirs(ENRICHED_OUTPUTS_DIR, exist_ok=True)
    except Exception as e:
        logger.error("Failed to create enriched outputs directory: %s", e)
        return

    if not os.path.exists(MODELS_DIR):
        logger.error("Models directory not found: %s", MODELS_DIR)
        return

    model_files = [f for f in os.listdir(MODELS_DIR) if f.endswith(".json")]
    logger.info("Found %s model files in %s.", len(model_files), MODELS_DIR)

    for i, filename in enumerate(model_files):
        file_path = os.path.join(MODELS_DIR, filename)
        logger.info("Processing file: %s (%s/%s)", filename, i + 1, len(model_files))

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                model_data = json.load(f)

            enriched_model_data = enrich_model_metadata(model_data)

            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(enriched_model_data, f, indent=2)
                logger.info("Successfully processed: %s", filename)
            except Exception as e:
                logger.error("Error writing enriched data to %s: %s", filename, e)

        except json.JSONDecodeError as e:
            logger.error("Error decoding JSON from %s: %s", filename, e)
        except Exception as e:
            logger.error("Error processing %s: %s", filename, e)

        time.sleep(0.1)

    logger.info("Model enrichment process completed.")


if __name__ == "__main__":
    if os.path.exists(str(LOG_FILE)):
        os.remove(str(LOG_FILE))
    main()
