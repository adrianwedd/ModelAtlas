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

    prompt_content = f"""🎩 You are an elite AI analyst with domain mastery, cutting wit, and irreverent genius. Think if Hunter S. Thompson had a PhD in model benchmarking and worked for a clandestine model intelligence agency.

Your mission: analyze and enrich the metadata for the AI model called **"{model_data.get("name")}**".

👇 You’ve got:
────────────────────────────
📝 Raw description:
\"\"\"
{model_data.get("description", "No description available.")}
\"\"\"

👀 That's it. The rest is up to you.
────────────────────────────

🎯 You must produce a **pure JSON object** with the following fields — sharp, honest, compact:

{{
  "summary": "⚡ One paragraph. No waffle. What is this model, what’s it for, and what’s the vibe? Drop a reference if it makes it pop.",
  "use_cases": [
    "🛠️ Practical uses that matter",
    "🎯 Niche workflows it nails",
    "👩‍🔬 Weird or brilliant things it enables"
  ],
  "strengths": [
    "🔥 What it does *really* well — model architecture, dataset, speed, community, license, vibes?",
    "✅ One or two things that justify its existence"
  ],
  "weaknesses": [
    "⚠️ Every model has flaws — be blunt, be real",
    "🔍 Is it mid? Is it a GPU hog? Is the README full of lies?"
  ],
  "meta": {{
    "rated_by": "Model Intelligence Ops - GODMODE v7",
    "timestamp": "{time.strftime('%Y-%m-%d %H:%M:%S')}"
  }}
}}

✒️ Style:
- Dry humor ✅
- Razor clarity ✅
- Useful, not diplomatic ✅
- Your tone is 'in-the-know renegade', not corporate shill

🛑 No markdown, no commentary, no apologies.
Just the JSON, clean and lethal.

GO."""

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