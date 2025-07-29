import json
from pathlib import Path
import sys
from typing import List, Dict

from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

# Add the project root to sys.path to enable imports from atlas_schemas
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from atlas_schemas.models import Model
from atlas_schemas.config import settings

console = Console()

def validate_model_file(file_path: Path) -> Dict:
    """Validates a single JSON file against the Model schema."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # If the file contains a list of models, validate each one
        if isinstance(data, list):
            for item in data:
                Model(**item) # Validate each item in the list
        else:
            Model(**data) # Validate single model
        return {"file": file_path.name, "status": "✅ Valid", "errors": "None"}
    except ValidationError as e:
        return {"file": file_path.name, "status": "❌ Invalid", "errors": str(e)}
    except json.JSONDecodeError as e:
        return {"file": file_path.name, "status": "❌ Invalid", "errors": f"JSON Decode Error: {e}"}
    except Exception as e:
        return {"file": file_path.name, "status": "❌ Invalid", "errors": f"Unexpected Error: {e}"}

def main() -> None:
    """Scans and validates all JSON files in enriched_outputs directory."""
    enriched_outputs_dir = settings.ENRICHED_OUTPUTS_DIR
    if not enriched_outputs_dir.exists():
        console.print(f"[bold red]Error: {enriched_outputs_dir} does not exist.[/]")
        sys.exit(1)

    json_files = list(enriched_outputs_dir.glob("*.json"))
    if not json_files:
        console.print(f"[bold yellow]No JSON files found in {enriched_outputs_dir}.[/]")
        sys.exit(0)

    results: List[Dict] = []
    all_valid = True

    for file_path in json_files:
        result = validate_model_file(file_path)
        results.append(result)
        if result["status"] == "❌ Invalid":
            all_valid = False

    table = Table(title="Schema Validation Results")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Errors", style="red")

    for res in results:
        table.add_row(res["file"], res["status"], res["errors"])

    console.print(table)

    if not all_valid:
        console.print("[bold red]Schema validation failed for some files.[/]")
        sys.exit(1)
    else:
        console.print("[bold green]All files passed schema validation.[/]")
        sys.exit(0)

if __name__ == "__main__":
    main()
