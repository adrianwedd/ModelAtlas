import asyncio
import glob
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, StateGraph

from common.logging import logger
from tools.enrich_metadata import enrich_model_metadata
from tools.scrape_hf import execute_hf_scraper
from tools.scrape_ollama import scrape_ollama_models
from tools.scrape_ollama_cloud import scrape_ollama_cloud_models
from tools.scrape_openrouter import scrape_openrouter_models
from tools.validate_all import validate_model_file


def _unix_to_iso(ts) -> str | None:
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    except (ValueError, TypeError, OSError):
        return None


# Define the state for our graph
class TraceState(TypedDict):
    raw_models_dir: Path
    enriched_models_dir: Path
    validated_models_dir: Path
    final_output_file: Path
    # Add other state variables as needed, e.g., errors, logs


# Define the nodes (functions) for each stage of the trace
async def scrape_node(state: TraceState) -> TraceState:
    logger.info("Executing Scrape Node...")
    raw_models_dir = state["raw_models_dir"]

    os.makedirs(raw_models_dir, exist_ok=True)

    if os.environ.get("ATLAS_SKIP_SCRAPE", "").lower() in ("true", "1", "yes"):
        logger.info("Skipping scrape as ATLAS_SKIP_SCRAPE is true.")
        return {"raw_models_dir": raw_models_dir}

    # Execute Hugging Face scraper
    logger.info("Starting Hugging Face scraping...")
    await asyncio.to_thread(
        execute_hf_scraper, limit=10, use_cache=True
    )  # Limit for testing, use_cache for efficiency
    logger.info("Hugging Face scraping complete.")

    # Execute Ollama scraper (ollama.com/library — locally-pullable models)
    logger.info("Starting Ollama library scraping...")
    await scrape_ollama_models(concurrency=5)
    logger.info("Ollama library scraping complete.")

    # Execute Ollama Cloud scraper (GPU-hosted cloud-only models via API)
    logger.info("Starting Ollama Cloud API scraping...")
    await asyncio.to_thread(scrape_ollama_cloud_models)
    logger.info("Ollama Cloud scraping complete.")

    # Execute OpenRouter scraper (200+ models, including free-tier)
    logger.info("Starting OpenRouter scraping...")
    await asyncio.to_thread(scrape_openrouter_models)
    logger.info("OpenRouter scraping complete.")

    return {"raw_models_dir": raw_models_dir}


def enrich_node(state: TraceState) -> TraceState:
    logger.info("Executing Enrich Node...")
    raw_models_dir = state["raw_models_dir"]
    enriched_models_dir = state["enriched_models_dir"]

    os.makedirs(enriched_models_dir, exist_ok=True)

    for file_path in glob.glob(str(raw_models_dir / "**/*.json"), recursive=True):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                model_data = json.load(f)

            if not model_data.get("source"):
                parent = Path(file_path).parent.name
                source_map = {
                    "huggingface": "huggingface",
                    "ollama": "ollama",
                    "ollama_cloud": "ollama_cloud",
                    "openrouter": "openrouter",
                }
                model_data["source"] = source_map.get(parent)

            enriched_data = enrich_model_metadata(model_data)

            # Use model's name field so merge_enrichment can find the file by name
            model_name_slug = model_data.get("name", Path(file_path).stem).replace(
                "/", "_"
            )
            output_path = enriched_models_dir / f"{model_name_slug}_enriched.json"
            if output_path.exists():
                logger.info(
                    "Enrichment file %s exists; skipping to preserve curated data.",
                    output_path.name,
                )
                continue
            tmp_fd, tmp_path = tempfile.mkstemp(
                dir=enriched_models_dir, suffix=".json.tmp"
            )
            try:
                with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                    json.dump(enriched_data, f, indent=2)
                    f.write("\n")
                os.replace(tmp_path, output_path)
            except Exception:
                os.unlink(tmp_path)
                raise
            logger.info(f"Enriched and saved: {output_path}")
        except Exception as e:
            logger.error(f"Error enriching model {file_path}: {e}")

    return {"enriched_models_dir": enriched_models_dir}


def validate_node(state: TraceState) -> TraceState:
    logger.info("Executing Validate Node...")
    enriched_models_dir = state["enriched_models_dir"]
    validated_models_dir = state["validated_models_dir"]

    os.makedirs(validated_models_dir, exist_ok=True)

    all_valid = True
    for file_path in glob.glob(str(enriched_models_dir / "*.json")):
        result = validate_model_file(Path(file_path))
        if result["status"] == "❌ Invalid":
            all_valid = False
            logger.error(
                "Validation failed for %s: %s", result["file"], result["errors"]
            )
        else:
            logger.info("Validation passed for %s", result["file"])
            # Copy valid files to the validated_models_dir
            with open(file_path, "r", encoding="utf-8") as f_in:
                data = json.load(f_in)
            with open(
                validated_models_dir / Path(file_path).name, "w", encoding="utf-8"
            ) as f_out:
                json.dump(data, f_out, indent=2)

    if not all_valid:
        logger.error("Some enriched models failed schema validation.")
        # Depending on desired behavior, you might raise an exception here
        # or proceed with only valid models.
    else:
        logger.info("All enriched models passed schema validation.")

    return {"validated_models_dir": validated_models_dir}


def score_node(state: TraceState) -> TraceState:
    logger.info("Executing Score Node...")
    validated_models_dir = state["validated_models_dir"]
    final_output_file = state["final_output_file"]

    from atlas_schemas.models import Model
    from trustforge import compute_score

    # Fields not in the Model schema but useful for trust scoring
    EXTRA_ANNOTATION_FIELDS = {
        "context_length",
        "is_free",
        "pricing",
        "provider",
        "display_name",
        "downloads",
    }

    scored_models = []
    for file_path in glob.glob(str(validated_models_dir / "*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Promote extra fields into annotations before Pydantic drops them
            ann = data.setdefault("annotations", {})
            for field in EXTRA_ANNOTATION_FIELDS:
                if field in data and field not in ann:
                    ann[field] = data[field]
            # Map HF downloads → pull_count when absent
            if not data.get("pull_count") and data.get("downloads"):
                data["pull_count"] = data["downloads"]
            # Map source-specific timestamp fields → last_updated
            if not data.get("last_updated"):
                data["last_updated"] = data.get("added_at") or _unix_to_iso(
                    data.get("created")
                )
            # Skip routing alias entries (OpenRouter ~name convention)
            if (data.get("name") or "").startswith("~"):
                continue
            model = Model(**data)
            # Strip junk tags: Ollama digest strings containing bullet char
            model.tags = [t for t in model.tags if "•" not in t and t != "latest"]
            model.trust_score = compute_score(model)
            scored_models.append(model.model_dump())
        except Exception as e:
            logger.error("Error scoring model %s: %s", file_path, e)

    os.makedirs(final_output_file.parent, exist_ok=True)
    with open(final_output_file, "w", encoding="utf-8") as f:
        json.dump(scored_models, f, indent=2)
        f.write("\n")
    logger.info(
        "Scored %s models, written to %s", len(scored_models), final_output_file
    )

    return {"final_output_file": final_output_file}


def visualize_node(state: TraceState) -> TraceState:
    logger.info("Executing Visualize Node (stub — not yet implemented).")
    return state


# Build the graph
def build_trace_graph():
    workflow = StateGraph(TraceState)

    workflow.add_node("scrape", scrape_node)
    workflow.add_node("enrich", enrich_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("score", score_node)
    workflow.add_node("visualize", visualize_node)

    workflow.set_entry_point("scrape")

    workflow.add_edge("scrape", "enrich")
    workflow.add_edge("enrich", "validate")
    workflow.add_edge("validate", "score")
    workflow.add_edge("score", "visualize")
    workflow.add_edge("visualize", END)

    return workflow.compile()
