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
from enrich.orchestrator import build_trace_graph, TraceState


def run_enrichment_trace(input_dir: Path, output_file: Path, enriched_outputs_dir: Path) -> None:
    graph = build_trace_graph()
    initial_state = TraceState(
        raw_models_dir=input_dir,
        enriched_models_dir=enriched_outputs_dir,
        validated_models_dir=Path("data/validated"), # Placeholder for now
        final_output_file=output_file,
    )
    # This is a simplified call. In a real scenario, you'd iterate through the graph stream
    # and handle state updates and actual function calls within the nodes.
    graph.invoke(initial_state)

# Removed if __name__ == "__main__" block