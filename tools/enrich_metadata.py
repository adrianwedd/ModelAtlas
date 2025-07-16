import json
import os
import re
import time

LOG_FILE = "enrichment.log"
MODELS_DIR = "models"
PROMPTS_DIR = "enrichment_prompts"
ENRICHED_OUTPUTS_DIR = "enriched_outputs"

def log_message(message, level="INFO", status=None, phase=None):
    """Append a timestamped log entry to LOG_FILE, with optional status and phase markers."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    status_str = f"[{status}]" if status else ""
    phase_str = f"[{phase}]" if phase else ""
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] [{level}]{phase_str}{status_str} {message}\n")

def enrich_model_metadata(model_data):
    """
    Generates prompts for subjective enrichment.
    """
    model_name = model_data.get("name", "unknown_model").replace('/', '_')
    
    # Generate prompt for subjective enrichment
    prompt_filename = os.path.join(PROMPTS_DIR, f"{model_name}_prompt.txt")
    enriched_output_filename = os.path.join(ENRICHED_OUTPUTS_DIR, f"{model_name}_enriched.json")

    prompt_content = f"""Please provide a concise summary, potential use cases, key strengths, and key weaknesses for the model: {model_data.get("name")}.

Here is its current description: {model_data.get("description", "No description available.")}

Format your response as a JSON object with the following keys:
{{
  "summary": "<concise summary>",
  "use_cases": ["<use case 1>", "<use case 2>"],
  "strengths": ["<strength 1>", "<strength 2>"],
  "weaknesses": ["<weakness 1>", "<weakness 2>"]
}}
"""

    with open(prompt_filename, "w", encoding="utf-8") as f:
        f.write(prompt_content)
    log_message(f"Generated enrichment prompt: {prompt_filename}", level="INFO")

    # Create placeholder for manual enrichment output
    placeholder_output = {
        "summary": "",
        "use_cases": [],
        "strengths": [],
        "weaknesses": []
    }
    with open(enriched_output_filename, "w", encoding="utf-8") as f:
        json.dump(placeholder_output, f, indent=2)
    log_message(f"Created enrichment output placeholder: {enriched_output_filename}", level="INFO")

    # Add paths to model_data for later reference
    model_data["enrichment_prompt_path"] = prompt_filename
    model_data["manual_enriched_output_path"] = enriched_output_filename

    return model_data

def main():
    log_message("Starting model enrichment process (prompt generation only).")
    
    os.makedirs(PROMPTS_DIR, exist_ok=True)
    os.makedirs(ENRICHED_OUTPUTS_DIR, exist_ok=True)

    if not os.path.exists(MODELS_DIR):
        log_message(f"Models directory not found: {MODELS_DIR}", level="ERROR")
        return

    model_files = [f for f in os.listdir(MODELS_DIR) if f.endswith(".json")]
    log_message(f"Found {len(model_files)} model files to process in {MODELS_DIR}.")

    for i, filename in enumerate(model_files):
        file_path = os.path.join(MODELS_DIR, filename)
        model_name_for_log = filename.replace(".json", "")
        log_message(f"Processing file: {filename} ({i+1}/{len(model_files)})", phase="enrichment")
        
        try:
            with open(file_path, 'r') as f:
                model_data = json.load(f)
            
            enriched_model_data = enrich_model_metadata(model_data)
            
            with open(file_path, 'w') as f:
                json.dump(enriched_model_data, f, indent=2)
            log_message(f"Successfully processed: {filename}")
        except json.JSONDecodeError as e:
            log_message(f"Error decoding JSON from {filename}: {e}", level="ERROR")
        except Exception as e:
            log_message(f"Error processing {filename}: {e}", level="ERROR")
        
        time.sleep(0.1) # Politeness delay

    log_message("Model enrichment process completed.", status="COMPLETE")

if __name__ == "__main__":
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    main()