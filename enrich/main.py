"""Simple enrichment trace that merges manual metadata and computes trust scores."""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from atlas_schemas.config import settings  # noqa: E402
from enrich.orchestrator import TraceState, build_trace_graph  # noqa: E402


def run_enrichment_trace(
    input_dir: Path, output_file: Path, enriched_outputs_dir: Path
) -> None:
    graph = build_trace_graph()
    initial_state = TraceState(
        raw_models_dir=input_dir,
        enriched_models_dir=enriched_outputs_dir,
        validated_models_dir=settings.PROJECT_ROOT / "data" / "validated",
        final_output_file=output_file,
    )
    asyncio.run(graph.ainvoke(initial_state))
