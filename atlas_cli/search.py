from pathlib import Path
from typing import List, Dict
import json

from rich.console import Console
from rich.table import Table

from atlas_schemas.config import settings

CATALOG_PATH = settings.PROJECT_ROOT / "models_enriched.json"
console = Console()

def load_models(catalog_path: Path = CATALOG_PATH) -> List[Dict]:
    """Load models from the given JSON file."""
    if not catalog_path.exists():
        console.print(f"[bold red]Catalog not found at {catalog_path}.[/]")
        return []
    with open(catalog_path, "r", encoding="utf-8") as f:
        return json.load(f)

def search_models(query: str, models: List[Dict], top_k: int = 5) -> List[Dict]:
    """Return top_k models matching the query."""
    if not models:
        return []
    q = query.lower()
    scored = []
    for m in models:
        text = f"{m.get('name', '')} {m.get('summary', '')}".lower()
        if q in text:
            score = text.count(q)
            scored.append((score, m))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored[:top_k]]

def display_results(models: List[Dict]) -> None:
    """Pretty print matching models."""
    table = Table(title="Matching Models")
    table.add_column("Name", style="cyan")
    table.add_column("Summary", style="green")
    for m in models:
        table.add_row(m.get("name", "?"), m.get("summary", "")[:50])
    console.print(table)

def cli(query: str, top_k: int = 5, catalog: Path = CATALOG_PATH) -> None:
    """Search models in the catalog and display results."""
    models = load_models(catalog)
    results = search_models(query, models, top_k=top_k)
    if results:
        display_results(results)
    else:
        console.print("[bold yellow]No matches found.[/]")
