import argparse
import json
import os
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from sentence_transformers import SentenceTransformer, util

# Load the model catalog
CATALOG_PATH = "models_enriched.json"

console = Console()
model = SentenceTransformer('all-MiniLM-L6-v2')  # ~80MB

def load_models():
    if not os.path.exists(CATALOG_PATH):
        console.print(f"[bold red]Catalog not found at {CATALOG_PATH}.[/]")
        return []
    with open(CATALOG_PATH) as f:
        return json.load(f)

def search_models(query, top_k=5):
    data = load_models()
    if not data:
        return []

    texts = [m['name'] + ": " + m.get('summary', '') for m in data]
    query_vec = model.encode(query, convert_to_tensor=True)
    doc_vecs = model.encode(texts, convert_to_tensor=True)

    hits = util.semantic_search(query_vec, doc_vecs, top_k=top_k)[0]
    results = [data[i['corpus_id']] for i in hits]
    return results

def display_results(models):
    table = Table(title="Matching Models")
    table.add_column("Name", style="cyan")
    table.add_column("Params (B)", justify="right")
    table.add_column("License", style="green")
    table.add_column("Trust Score", justify="right")

    for m in models:
        table.add_row(
            m['name'],
            str(m.get('params_b', '?')),
            m.get('license', '?'),
            str(m.get('trust', {}).get('score', '?'))
        )
    console.print(table)

def main():
    parser = argparse.ArgumentParser(description="Semantic search across Ollama model catalog")
    parser.add_argument("query", type=str, help="Your natural language search query")
    parser.add_argument("--top_k", type=int, default=5, help="Number of top results to return")

    args = parser.parse_args()
    results = search_models(args.query, args.top_k)
    if results:
        display_results(results)
    else:
        console.print("[bold yellow]No matches found.[/]")

if __name__ == "__main__":
    main()
