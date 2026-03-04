import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def test_enrich_node_no_collision_across_subdirs(tmp_path):
    """Two models with the same filename in different subdirs must produce distinct output files."""
    from enrich.orchestrator import enrich_node

    # Create two models with same filename in different subdirs
    hf_dir = tmp_path / "raw" / "huggingface"
    ol_dir = tmp_path / "raw" / "ollama"
    hf_dir.mkdir(parents=True)
    ol_dir.mkdir(parents=True)

    (hf_dir / "bert.json").write_text(json.dumps({"name": "bert-hf"}))
    (ol_dir / "bert.json").write_text(json.dumps({"name": "bert-ol"}))

    enriched_dir = tmp_path / "enriched"
    enriched_dir.mkdir()

    state = {
        "raw_models_dir": tmp_path / "raw",
        "enriched_models_dir": enriched_dir,
        "validated_models_dir": tmp_path / "validated",
        "final_output_file": tmp_path / "out.json",
    }

    with patch("enrich.orchestrator.enrich_model_metadata", side_effect=lambda d: d):
        enrich_node(state)

    output_files = list(enriched_dir.glob("*.json"))
    assert len(output_files) == 2, (
        f"Expected 2 outputs (no collision), got {len(output_files)}: "
        f"{[f.name for f in output_files]}"
    )


def test_orchestrator_has_no_main_block():
    """The orchestrator must not have a dead __main__ block."""
    src = (PROJECT_ROOT / "enrich" / "orchestrator.py").read_text()
    # The dead block starts with building an initial_state dict with hardcoded paths
    assert '"models/raw"' not in src, "Dead __main__ block still present"
