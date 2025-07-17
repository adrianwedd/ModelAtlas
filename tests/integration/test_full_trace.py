import pytest
import subprocess
import os
import json

# Define paths relative to the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ATLAS_CLI_PATH = os.path.join(PROJECT_ROOT, "atlas_cli", "main.py") # Assuming atlas_cli/main.py is the entry point

@pytest.fixture
def sample_input_file(tmp_path):
    """Creates a dummy input file for the trace."""
    input_data = [
        {"id": "model1", "content": "This is a sample model description."},
        {"id": "model2", "content": "Another model with different content."}
    ]
    file_path = tmp_path / "sample_input.jsonl"
    with open(file_path, "w") as f:
        for item in input_data:
            f.write(json.dumps(item) + "\n")
    return file_path

@pytest.fixture
def fixture_tasks_yml(tmp_path):
    """Creates a dummy tasks.yml for the trace."""
    tasks_content = """
- id: 1
  title: "Dummy Task 1"
  description: "A placeholder task."
  component: "Test"
  dependencies: []
  priority: 1
  status: "pending"
  command: "echo 'Task 1 executed'"
  execution:
    tool: "shell_command"
    args: {}
  task_id: "TEST-001"
  area: "Test"
  actionable_steps: []
  acceptance_criteria: []
  assigned_to: "TestRunner"
  ci_notes: ""
  epic: "Test"
"""
    file_path = tmp_path / "tasks.yml"
    with open(file_path, "w") as f:
        f.write(tasks_content)
    return file_path

def test_full_trace_execution(sample_input_file, fixture_tasks_yml, tmp_path):
    """Tests the end-to-end execution of a full trace."""
    output_file = tmp_path / "output.jsonl"

    # Assuming atlas_cli takes input and output paths, and a tasks.yml path
    # This command needs to be adjusted based on the actual atlas_cli interface
    command = [
        "python",
        ATLAS_CLI_PATH,
        "--input", str(sample_input_file),
        "--output", str(output_file),
        "--tasks_yml", str(fixture_tasks_yml)
    ]

    try:
        # Execute the CLI command
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        pytest.fail(f"Full trace execution failed: {e}")

    # Assert that the output file is created
    assert output_file.exists()
    assert output_file.stat().st_size > 0 # Ensure it's not empty

    # Optionally, assert content of the output file
    with open(output_file, "r") as f:
        output_content = [json.loads(line) for line in f]
    assert len(output_content) > 0
    # Further assertions on the content structure or values can be added here
