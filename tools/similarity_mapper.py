import json
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Placeholder for an actual embedding model
def get_embedding(text: str) -> List[float]:
    # In a real scenario, this would use a pre-trained embedding model
    # For now, a simple hash-based vector for demonstration
    hash_val = sum(ord(c) for c in text) % 1000
    return [float(hash_val) / 1000.0] * 768 # Dummy 768-dim vector

def compute_similarity(models: List[Dict]) -> List[Dict]:
    if not models:
        return []

    # Generate embeddings for summaries
    summaries = [m.get("summary", "") for m in models]
    embeddings = np.array([get_embedding(s) for s in summaries])

    # Compute cosine similarity
    similarity_matrix = cosine_similarity(embeddings)

    updated_models = []
    for i, model in enumerate(models):
        similar_indices = similarity_matrix[i].argsort()[-6:-1][::-1] # Top 5 excluding self
        similar_models_list = []
        for idx in similar_indices:
            if i != idx: # Ensure not adding self
                similar_models_list.append({
                    "name": models[idx].get("name"),
                    "score": round(similarity_matrix[i][idx], 4)
                })
        model["similar_models"] = similar_models_list
        updated_models.append(model)
    return updated_models

def main(input_path: Path, output_path: Path):
    if not input_path.exists():
        print(f"Error: Input file not found at {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        models_data = json.load(f)

    updated_models_data = compute_similarity(models_data)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(updated_models_data, f, indent=2)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compute model similarity and populate `similar_models`.")
    parser.add_argument("--input", type=Path, default=Path("data/models_validated.json"),
                        help="Path to the input JSON file containing validated models.")
    parser.add_argument("--output", type=Path, default=Path("data/models_similar.json"),
                        help="Path to the output JSON file for models with similarity data.")
    args = parser.parse_args()

    main(args.input, args.output)
