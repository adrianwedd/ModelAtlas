from huggingface_hub import list_models, HfApi, ModelCard, hf_hub_download
import json
import os
import time
import re
import sys

LOG_FILE = "hf_scraper.log"
# OUTPUT_FILE = "data/models_raw.json" # Removed, as we're saving individual files

def log_message(message, level="INFO", status=None, phase=None):
    """Append a timestamped log entry to LOG_FILE, with optional status and phase markers."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    status_str = f"[{status}]" if status else ""
    phase_str = f"[{phase}]" if phase else ""
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] [{level}]{phase_str}{status_str} {message}\n")

def parse_pull_count(s):
    """Normalize text counts like '1.2M' or '650K' into integer counts."""
    if isinstance(s, (int, float)):
        return int(s)
    if not s:
        return 0
    s = str(s).replace("Downloads", "").strip()
    try:
        if "M" in s:
            return int(float(s.replace("M"," ")) * 1e6)
        if "K" in s:
            return int(float(s.replace("K"," ")) * 1e3)
        return int(float(s))
    except:
        return 0  # fallback to zero on parse failure

def run_hf_scraper(limit=None):
    api = HfApi()
    all_models_data = []
    
    log_message("Starting Hugging Face Hub scraping...")
    
    # Define the new output directory for Hugging Face models
    hf_models_output_dir = os.path.join("models", "huggingface")
    os.makedirs(hf_models_output_dir, exist_ok=True)

    try:
        # Fetch models from Hugging Face Hub
        hf_models_list = list(list_models(sort="downloads", direction=-1, limit=limit))
        log_message(f"Fetched {len(hf_models_list)} models from Hugging Face Hub initial list.")

        for i, model_info in enumerate(hf_models_list):
            model_id = model_info.id
            log_message(f"Processing model: {model_id} ({i+1}/{len(hf_models_list)})", phase="hf_scrape")
            
            try:
                # Fetch full model details
                full_model_info = api.model_info(model_id)
                
                # Use .get() with a default empty dictionary if cardData is None
                card_data = full_model_info.cardData if full_model_info.cardData is not None else {}

                # Extract relevant data points
                data = {
                    "name": full_model_info.id,
                    "description": card_data.get("description", ""),
                    "downloads": parse_pull_count(full_model_info.downloads),
                    "last_updated": full_model_info.lastModified.isoformat() if full_model_info.lastModified else None,
                    "license": card_data.get("license", ""),
                    "architecture": card_data.get("architecture", ""),
                    "family": card_data.get("model_name", ""), # Often model_name in cardData is the family
                    "tags": full_model_info.tags,
                    "model_variants": [] # To store detailed tag info if available
                }

                # Attempt to get more detailed info from model card if available
                try:
                    model_card = ModelCard.load(model_id)
                    if model_card.data:
                        # Extracting specific details from model card data
                        if "model-index" in model_card.data:
                            for item in model_card.data["model-index"]:
                                if "results" in item:
                                    for result in item["results"]:
                                        if "metrics" in result:
                                            for metric in result["metrics"]:
                                                if "name" in metric and "value" in metric:
                                                    if "benchmarks" not in data:
                                                        data["benchmarks"] = {}
                                                    data["benchmarks"][metric["name"]] = metric["value"]
                        
                        # Extract arxiv links from model card content (README.md)
                        arxiv_links = re.findall(r'arxiv:([0-9]{4}\.[0-9]{5})', model_card.content)
                        if arxiv_links:
                            data["arxiv_ids"] = list(set(arxiv_links)) # Use set to avoid duplicates

                except Exception as mc_e:
                    log_message(f"Could not load model card for {model_id}: {mc_e}", level="WARNING")

                all_models_data.append(data)

                # Save individual model JSON file in the new directory
                model_file_path = os.path.join(hf_models_output_dir, f"{model_id.replace('/', '_')}.json")
                with open(model_file_path, "w") as mf:
                    json.dump(data, mf, indent=2)

            except Exception as model_e:
                log_message(f"Error processing model {model_id}: {model_e}", level="ERROR")
            
            time.sleep(0.1) # Politeness delay

    except Exception as e:
        log_message(f"An error occurred during Hugging Face Hub scraping: {e}", level="ERROR")

    log_message(f"Hugging Face Hub scraping complete — {len(all_models_data)} models stored in {hf_models_output_dir}", status="COMPLETE", phase="done")

if __name__ == "__main__":
    # Reset log file each run for clean debugging
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    
    # Example usage: scrape top 100 models
    run_hf_scraper(limit=100)
