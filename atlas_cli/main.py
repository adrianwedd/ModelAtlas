from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Optional

import yaml
import typer
from rich.console import Console
from rich.panel import Panel

# Add the project root to sys.path to enable imports from atlas_schemas
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from common.logging import logger
from atlas_schemas.config import settings
from enrich.main import run_enrichment_trace
from trustforge.score import compute_and_merge_trust_scores

app = typer.Typer(help="ModelAtlas CLI")
console = Console()


@app.command(help="Run the enrichment and trust score trace.")
def trace(
    input: Optional[Path] = typer.Option(None, help="Input file path"),
    output: Optional[Path] = typer.Option(None, help="Output file path"),
    tasks_yml: Optional[Path] = typer.Option(None, help="Tasks YAML file path"),
) -> None:
    """Run the enrichment and trust score trace.

    Examples:
        python -m atlas_cli.main trace --input models --output result.json
    """
    tasks_file_path = tasks_yml if tasks_yml else PROJECT_ROOT / "tasks.yml"
    if not tasks_file_path.exists():
        logger.error("tasks.yml not found at %s", tasks_file_path)
        raise typer.Exit(code=1)

    with open(tasks_file_path, "r", encoding="utf-8") as f:
        tasks = yaml.safe_load(f)

    input_path = input if input else settings.MODELS_DIR
    output_path = output if output else (settings.PROJECT_ROOT / settings.OUTPUT_FILE)

    for task in tasks:
        if task["id"] == 2:
            logger.info("Executing Task %s: %s", task["id"], task["title"])
            run_enrichment_trace(
                input_dir=input_path,
                output_file=output_path,
                enriched_outputs_dir=settings.ENRICHED_OUTPUTS_DIR,
            )
        elif task["id"] == 10:
            logger.info("Executing Task %s: %s", task["id"], task["title"])
            compute_and_merge_trust_scores(
                input_dir=input_path,
                output_file=output_path,
                enriched_outputs_dir=settings.ENRICHED_OUTPUTS_DIR,
            )

    logger.info("Trace execution complete.")


@app.command(help="Bootstrap local environment by creating a .env file.")
def init() -> None:
    """Bootstrap local environment by creating a .env file.

    Example:
        python -m atlas_cli.main init
    """
    env_path = PROJECT_ROOT / ".env"
    example_path = PROJECT_ROOT / ".env.example"
    if env_path.exists():
        console.print(f"[yellow].env already exists at {env_path}[/]")
    else:
        shutil.copy(example_path, env_path)
        console.print(Panel("TRUTH FORGED", style="bold green"))
        console.print(f"[bold green]Created {env_path} from .env.example[/]")


def _run() -> None:
    args = sys.argv[1:]
    if args and args[0] in {"init", "trace", "--help", "-h"}:
        app()
    else:
        app(args=["trace"] + args)


if __name__ == "__main__":
    _run()
