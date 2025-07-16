
import argparse
import json
import requests

def ollama_request(model, prompt):
    """
    Sends a request to the Ollama API.
    """
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

def enrich_model_metadata(model_name):
    """
    Enriches model metadata using a local Ollama instance.
    """
    prompt = f"Provide a brief summary, potential use cases, strengths, and weaknesses for the {model_name} model."
    return ollama_request("deepseek-r1:1.5b", prompt)

def main():
    parser = argparse.ArgumentParser(description="Enrich model metadata using a local Ollama instance.")
    parser.add_argument("--input", required=True, help="Path to the input JSON file with raw model data.")
    parser.add_argument("--output", required=True, help="Path to the output JSON file for enriched model data.")
    args = parser.parse_args()

    # Pull the deepseek-r1:1.5b model unless it exists
    print("Pulling deepseek-r1:1.5b model...")
    try:
        requests.get("http://localhost:11434/api/models/deepseek-r1:1.5b")
    except requests.exceptions.RequestException as e:
        try:
            requests.post("http://localhost:11434/api/pull", json={"name": "deepseek-r1:1.5b"})
        except requests.exceptions.RequestException as e:
            print(f"Could not pull deepseek-r1:1.5b model. Is Ollama running? Error: {e}")
            return

    with open(args.input, 'r') as f:
        models = json.load(f)

    enriched_models = []
    for model in models:
        print(f"Enriching {model['name']}...")
        enriched_data = enrich_model_metadata(model['name'])
        model['enrichment'] = enriched_data
        enriched_models.append(model)

    with open(args.output, 'w') as f:
        json.dump(enriched_models, f, indent=2)

if __name__ == "__main__":
    main()
