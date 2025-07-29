from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
from pathlib import Path

# Define the state for our graph
class TraceState(TypedDict):
    raw_models_dir: Path
    enriched_models_dir: Path
    validated_models_dir: Path
    final_output_file: Path
    # Add other state variables as needed, e.g., errors, logs

# Define the nodes (functions) for each stage of the trace
def scrape_node(state: TraceState) -> TraceState:
    print("Executing Scrape Node...")
    # Call scrape_hf and scrape_ollama here
    # Update state with paths to raw models
    return {"raw_models_dir": state["raw_models_dir"]}

def enrich_node(state: TraceState) -> TraceState:
    print("Executing Enrich Node...")
    # Call run_enrichment_trace here
    # Update state with paths to enriched models
    return {"enriched_models_dir": state["enriched_models_dir"]}

def validate_node(state: TraceState) -> TraceState:
    print("Executing Validate Node...")
    # Call normalize_and_validate here
    # Update state with paths to validated models
    return {"validated_models_dir": state["validated_models_dir"]}

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
