"""
✨ Metadata Enrichment Script ✨

This script breathes life into your scraped model data using local LLM enrichment via Ollama.
Each model gets a lovingly crafted summary, showcasing its strengths, weaknesses, and use cases —
all wrapped in AI sass and JSON goodness. Designed with care by the ModelAtlas crew 💖
"""

import argparse
import json
import requests

# Function: ollama_request
# Purpose: Ask the local LLM to generate an answer based on the given prompt and model.
# If Ollama is asleep or something breaks, we don’t panic — we return the error message as-is.
def ollama_request(model, prompt):
    try:
        # Send a POST request to the Ollama API to generate text based on the prompt
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            }
        )
        # Raise an exception if the request failed (e.g. bad status code)
        response.raise_for_status()
        # Return the generated response text from the API
        return response.json()["response"]
    except requests.exceptions.RequestException as e:
        # If something goes wrong (network issue, API down), return the error message as a string
        return f"Error: {e}"

# Function: enrich_model_metadata
# Purpose: Calls ollama_request with a beautifully structured prompt full of rebel genius.
def enrich_model_metadata(model_name):
    prompt = f"""
You are a developer whisperer. Summarize {model_name} like you’re explaining it to someone smart, impatient, and caffeinated:

- Overview: What is it? How does it work? Why should we care?
- Strengths: List the top 3 things that make this model worth its VRAM.
- Use Cases: Show me where this thing shines. At least 3 examples, please.
- Similar Models: Name 2–3 other models that hang out in the same semantic playground. Think Hugging Face, arXiv—no posers.
"""
    return ollama_request("deepseek-r1:1.5b", prompt)

def main():
    # Parse CLI arguments with a friendly description
    parser = argparse.ArgumentParser(description="Enrich model metadata using a local Ollama instance.")
    parser.add_argument("--input", required=True, help="Path to the input JSON file with raw model data.")
    parser.add_argument("--output", required=True, help="Path to the output JSON file for enriched model data.")
    args = parser.parse_args()

    # 🔄 Ensuring deepseek-r1:1.5b is available locally for enrichment magic
    print("🔄 Ensuring deepseek-r1:1.5b is available...")
    try:
        # Check if the model is already pulled by querying the correct endpoint
        requests.get("http://localhost:11434/api/models/deepseek-r1:1.5b")
    except requests.exceptions.RequestException:
        # If not available, attempt to pull it with love and patience
        try:
            requests.post("http://localhost:11434/api/pull", json={"name": "deepseek-r1:1.5b"})
        except requests.exceptions.RequestException as e:
            print(f"❌ Could not pull deepseek-r1:1.5b model. Is Ollama running? Error: {e}")
            return

    # 📥 Load the raw model list from the provided input JSON file
    with open(args.input, 'r') as f:
        models = json.load(f)

    enriched_models = []
    for model in models:
        # ✨ Decorative header for friendlier logs before enriching each model
        print(f"\n✨ Enriching {model['name']} ✨")
        enriched_data = enrich_model_metadata(model['name'])  # 🧠 AI-generated enrichment
        model['enrichment'] = enriched_data
        enriched_models.append(model)

    # 💾 Save the enriched dataset to the output JSON file with pretty formatting
    with open(args.output, 'w') as f:
        json.dump(enriched_models, f, indent=2)

if __name__ == "__main__":
    main()
