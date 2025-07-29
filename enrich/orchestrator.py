import json
import glob
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
from pathlib import Path

from tools.enrich_metadata import enrich_model_metadata
from tools.scrape_hf import execute_hf_scraper
from tools.scrape_ollama import scrape_ollama_models
from tools.validate_all import validate_model_file
from common.logging import logger
import asyncio
import os

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

    # Execute Hugging Face scraper
    logger.info("Starting Hugging Face scraping...")
    execute_hf_scraper(limit=10, use_cache=True) # Limit for testing, use_cache for efficiency
    logger.info("Hugging Face scraping complete.")

    # Execute Ollama scraper
    logger.info("Starting Ollama scraping...")
    await scrape_ollama_models(concurrency=5) # Concurrency for async operations
    logger.info("Ollama scraping complete.")

    return {"raw_models_dir": raw_models_dir}

def enrich_node(state: TraceState) -> TraceState:
    logger.info("Executing Enrich Node...")
    raw_models_dir = state["raw_models_dir"]
    enriched_models_dir = state["enriched_models_dir"]
    
    os.makedirs(enriched_models_dir, exist_ok=True)

    for file_path in glob.glob(str(raw_models_dir / "**/*.json"), recursive=True):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
            
            enriched_data = enrich_model_metadata(model_data)
            
            # Save enriched data to the enriched_models_dir
            model_name = Path(file_path).stem # Get filename without extension
            output_path = enriched_models_dir / f"{model_name}_enriched.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(enriched_data, f, indent=2)
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
            logger.error(f"Validation failed for {result["file"]}: {result["errors"]}")
        else:
            logger.info(f"Validation passed for {result["file"]}")
            # Copy valid files to the validated_models_dir
            with open(file_path, 'r', encoding='utf-8') as f_in:
                data = json.load(f_in)
            with open(validated_models_dir / Path(file_path).name, 'w', encoding='utf-8') as f_out:
                json.dump(data, f_out, indent=2)

    if not all_valid:
        logger.error("Some enriched models failed schema validation.")
        # Depending on desired behavior, you might raise an exception here
        # or proceed with only valid models.
    else:
        logger.info("All enriched models passed schema validation.")

    return {"validated_models_dir": validated_models_dir}

def score_node(state: TraceState) -> TraceState:
    print("Executing Score Node...")
    # Call compute_and_merge_trust_scores here
    return state

def visualize_node(state: TraceState) -> TraceState:
    print("Executing Visualize Node...")
    # Call gen_viz here
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

if __name__ == "__main__":
    graph = build_trace_graph()
    # Example usage (replace with actual paths and logic)
    initial_state = {
        "raw_models_dir": Path("models/raw"),
        "enriched_models_dir": Path("enriched_outputs"),
        "validated_models_dir": Path("data/validated"),
        "final_output_file": Path("final_report.json"),
    }
    # For demonstration, we'll just run the graph without actual file operations
    # for s in graph.stream(initial_state):
    #     print(s)
