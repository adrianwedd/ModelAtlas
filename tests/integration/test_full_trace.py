import pytest
import subprocess
import os
import json
from pathlib import Path
import sys

# Add the project root to sys.path to enable imports from atlas_schemas
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from common.logging import logger

# Define paths relative to the project root
ATLAS_CLI_PATH = PROJECT_ROOT / "atlas_cli" / "main.py"

@pytest.fixture
def sample_input_dir(tmp_path):
    """Creates a dummy input directory with model JSON files."""
    input_data_model1 = {
        "name": "model1",
        "description": "This is a sample model description.",
        "pull_count": 1000,
        "license": "MIT",
        "tags": ["tag1", "tag2"]
    }
    input_data_model2 = {
        "name": "model2",
        "description": "Another model with different content.",
        "pull_count": 500,
        "license": "Apache-2.0",
        "tags": ["tag3"]
    }

    models_dir = tmp_path / "models"
    models_dir.mkdir()

    with open(models_dir / "model1.json", "w") as f:
        json.dump(input_data_model1, f)
    with open(models_dir / "model2.json", "w") as f:
        json.dump(input_data_model2, f)

    return models_dir

@pytest.fixture
def fixture_tasks_yml(tmp_path):
    """Creates a realistic tasks.yml for the trace."""
    tasks_content = """
- id: 2
  title: "Enrich model metadata with LLM"
  description: "Use prompt engineering to generate model summaries, use cases, strengths, and potential limitations."
  component: "LLMEnricher"
  dependencies: [1]
  priority: 2
  status: "pending"
  command: "python tools/enrich_metadata.py"
  execution:
    tool: "enrich_metadata"
    args:
      input: "data/models_raw.json"
      output: "data/models_enriched.json"
  task_id: "OLLAMA-002"
  area: "Semantic Enrichment"
  actionable_steps:
    - "Design prompts to extract developer-friendly model summaries"
    - "Include comparisons with similar models"
    - "Extract strengths and weaknesses heuristically"
  acceptance_criteria:
    - "Each model in models_enriched.json has summary, strengths, weaknesses, and use_cases"
    - "Generated content passes hallucination check"
  assigned_to: "LLMEnricher"
  ci_notes: "⚙️ Optimized for GitHub Actions: ensure script runtime < 6 mins, use minimal dependencies, write to /tmp or workspace only."
  epic: "Metadata Enrichment"

- id: 10
  title: "Evaluate and rank models by trust and transparency"
  description: "Use risk heuristics and download metadata to rank models by transparency and reliability."
  component: "TrustRanker"
  dependencies: [3]
  priority: 3
  status: "pending"
  command: "python tools/rank_trust.py"
  execution:
    tool: "rank_trust"
    args: {}
  task_id: "OLLAMA-010"
  area: "Model Intelligence"
  actionable_steps:
    - "Parse download metrics"
    - "Apply transparency heuristics from RISK_HEURISTICS.md"
    - "Calculate composite trust scores"
  acceptance_criteria:
    - "Each model has a trust_score"
    - "Top-10 table appears in README"
  assigned_to: "TrustRanker"
  ci_notes: "⚙️ Optimized for GitHub Actions: ensure script runtime < 6 mins, use minimal dependencies, write to /tmp or workspace only."
  epic: "Metadata Enrichment"
"""
    file_path = tmp_path / "tasks.yml"
    with open(file_path, "w") as f:
        f.write(tasks_content)
    return file_path

@pytest.fixture
def enriched_outputs_dir(tmp_path):
    """Creates a dummy enriched_outputs directory."""
    dir_path = tmp_path / "enriched_outputs"
    dir_path.mkdir()
    # Create dummy enriched files if needed for testing merge_enrichment
    # For now, we'll assume no pre-existing enriched data for simplicity
    return dir_path

def test_full_trace_execution(sample_input_dir, fixture_tasks_yml, enriched_outputs_dir, tmp_path):
    """Tests the end-to-end execution of a full trace."""
    output_file = tmp_path / "models_enriched.json"

    command = [
        "python",
        str(ATLAS_CLI_PATH),
        "trace",
        "--input", str(sample_input_dir),
        "--output", str(output_file),
        "--tasks-yml", str(fixture_tasks_yml)
    ]

    try:
        # Execute the CLI command
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info("STDOUT: %s", result.stdout)
        logger.info("STDERR: %s", result.stderr)

    except subprocess.CalledProcessError as e:
        logger.error("Command failed with exit code %s", e.returncode)
        logger.error("STDOUT: %s", e.stdout)
        logger.error("STDERR: %s", e.stderr)
        pytest.fail(f"Full trace execution failed: {e}")

    # Assert that the output file is created
    assert output_file.exists()
    assert output_file.stat().st_size > 0 # Ensure it's not empty

    # Assert content of the output file
    with open(output_file, "r") as f:
        output_content = json.load(f)

    assert isinstance(output_content, list)
    assert len(output_content) == 2 # Expecting 2 models

    # Check if trust_score is added and other fields are present
    for model in output_content:
        assert "name" in model
        assert "description" in model
        assert "trust_score" in model
        assert isinstance(model["trust_score"], float)
        assert 0.0 <= model["trust_score"] <= 1.0