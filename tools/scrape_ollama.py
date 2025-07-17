from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import json, sys, re, time, hashlib, os
import requests
from pathlib import Path
import requests_cache

from atlas_schemas.config import settings

LOG_FILE = settings.LOG_FILE
OLLAMA_MODELS_DIR = settings.MODELS_DIR / "ollama"
DEBUG_DIR = settings.DEBUG_DIR
CACHE_PATH = Path(settings.PROJECT_ROOT / ".cache" / "http")

LAYER_MEDIA_TYPE_MAP = {
    "application/vnd.ollama.image.model": "Model Weights",
    "application/vnd.ollama.image.license": "License",
    "application/vnd.ollama.image.template": "Template",
    "application/vnd.ollama.image.params": "Parameters",
}

def normalize_layer_media_type(media_type_str: str) -> str:
    """
    Normalizes a layer media type string to a friendly label.
    """
    if not media_type_str:
        return None
    return LAYER_MEDIA_TYPE_MAP.get(media_type_str, media_type_str)

LICENSE_MAP = {
    "mit": "MIT",
    "apache-2.0": "Apache-2.0",
}

def normalize_license(license_str: str) -> str:
    """
    Normalizes a license string to its SPDX ID.
    """
    if not license_str:
        return None
    license_str = license_str.lower().strip()
    return LICENSE_MAP.get(license_str, license_str)

def convert_size_to_gb(size_str: str) -> float:
    """
    Converts a size string (e.g., '3.8GB', '7.4MB') to gigabytes (float).
    """
    if not size_str:
        return None
    size_str = size_str.strip().upper()
    num = float(re.findall(r'\d+\.?\d*', size_str)[0])
    if "GB" in size_str:
        return num
    elif "MB" in size_str:
        return num / 1024
    elif "KB" in size_str:
        return num / (1024 * 1024)
    else:
        return None

def classify_with_llm(text: str) -> list:
    """
    Placeholder for LLM-based classification of text.
    In a real scenario, this would call an LLM API to infer topics/capabilities.
    """
    if "chat" in text.lower():
        return ["chatbot", "conversational AI"]
    elif "code" in text.lower():
        return ["code generation", "programming"]
    else:
        return ["general purpose"]

def quality_score(model_data: dict) -> dict:
    """
    Calculates a completeness score for the model data.
    """
    fields = [
        'name', 'description', 'license', 'pull_count', 'tags', 'readme_text',
        'architecture', 'family', 'page_hash'
    ]
    filled = sum(1 for f in fields if model_data.get(f))
    if "tags" in model_data and isinstance(model_data["tags"], list):
        for tag_entry in model_data["tags"]:
            if tag_entry.get("tag") and tag_entry.get("digest") and tag_entry.get("size"):
                filled += 1
            if tag_entry.get("config") and tag_entry["config"].get("parameters"):
                filled += 1
    total_possible = len(fields) + len(model_data.get("tags", [])) * 2
    completeness = round(filled / total_possible, 2) if total_possible > 0 else 0
    return {
        "fields_filled": filled,
        "total_possible": total_possible,
        "completeness": completeness
    }

def post_process_model_data(detail: dict) -> dict:
    """
    Performs any final post-processing on the model data before saving.
    """
    detail["quality_score"] = quality_score(detail)
    return detail


def log_message(message, level="INFO", status=None, phase=None):
    """Append a timestamped log entry to LOG_FILE, with optional status and phase markers."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    status_str = f"[{status}]" if status else ""
    phase_str = f"[{phase}]" if phase else ""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] [{level}]{phase_str}{status_str} {message}\n")

def parse_pull_count(s):
    """Normalize text counts like '1.2M' or '650K' into integer counts."""
    if not s:
        return 0
    s = s.replace("Pulls", "").replace("Downloads", "").strip()
    try:
        if "M" in s:
            return int(float(s.replace("M"," ")) * 1e6)
        if "K" in s:
            return int(float(s.replace("K"," ")) * 1e3)
        return int(float(s))
    except:
        return 0  # fallback to zero on parse failure

def get_hash(text):
    """Compute a 12-character SHA256 hash for change detection."""
    return hashlib.sha256(text.encode()).hexdigest()[:12]

def fetch_manifest(model, tag="latest"):
    """
    Fetches the manifest JSON from Ollama's registry API.
    """
    url = f"https://registry.ollama.ai/v2/library/{model}/manifests/{tag}"
    try:
        log_message(f"Fetching manifest from: {url}", phase="manifest_api")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        log_message(f"Error fetching manifest for {model}:{tag} from API: {e}", level="ERROR", phase="manifest_api")
        return None

def decode_manifest_config(model_name, config_digest):
    """
    Fetches and decodes the config blob associated with a manifest digest.
    """
    url = f"https://registry.ollama.ai/v2/library/{model_name}/blobs/{config_digest}"
    try:
        log_message(f"Fetching config blob from: {url}", phase="config_blob_api")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        log_message(f"Error fetching config blob for {model_name} with digest {config_digest}: {e}", level="ERROR", phase="config_blob_api")
        return None

def decode_manifest_config(model_name, config_digest):
    """
    Fetches and decodes the config blob associated with a manifest digest.
    """
    url = f"https://registry.ollama.ai/v2/library/{model_name}/blobs/{config_digest}"
    try:
        log_message(f"Fetching config blob from: {url}", phase="config_blob_api")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        log_message(f"Error fetching config blob for {model_name} with digest {config_digest}: {e}", level="ERROR", phase="config_blob_api")
        return None

def scrape_tags_page(page, model_name):
    """
    Scrapes the tags page for a given model to extract version information.
    """
    url = f"https://ollama.com/library/{model_name}/tags"
    tags_data = []
    try:
        log_message(f"Fetching tags page: {url}")
        page.goto(url, wait_until="networkidle", timeout=60000)
        soup = BeautifulSoup(page.content(), "html.parser")

        tag_items = soup.select("div.group.px-4.py-3")
        log_message(f"Found {len(tag_items)} tag items on the page.")

        for item in tag_items:
            # Prioritize desktop view as it has cleaner data
            desktop_view = item.find("div", class_=lambda c: c and "md:flex" in c.split())
            
            tag_name = ""
            size = ""
            digest = ""
            last_updated = ""

            if desktop_view:
                tag_name_element = desktop_view.find('a')
                tag_name = tag_name_element.get_text(strip=True) if tag_name_element else ''

                size_element = desktop_view.find("p", class_="col-span-2")
                size = size_element.get_text(strip=True) if size_element else ""

                details_div = desktop_view.find("div", class_="flex text-neutral-500 text-xs items-center")
                if details_div:
                    digest_element = details_div.find("span", class_="font-mono")
                    digest = digest_element.get_text(strip=True) if digest_element else ""
                    
                    last_updated_text = details_div.get_text(strip=True)
                    last_updated_match = re.search(r'·\s*(.*)', last_updated_text)
                    if last_updated_match:
                        last_updated = last_updated_match.group(1).strip()
            else:
                # Fallback to mobile view
                mobile_view = item.find("a", class_=lambda c: c and "md:hidden" in c.split())
                if mobile_view:
                    tag_name_element = mobile_view.find("span", class_="group-hover:underline")
                    tag_name = tag_name_element.get_text(strip=True) if tag_name_element else ''
                    
                    details_text = mobile_view.get_text(separator=' ', strip=True)
                    
                    size_match = re.search(r'•\s*([\d.]+\s*(?:GB|MB|KB))', details_text)
                    size = size_match.group(1) if size_match else ''

                    digest_match = re.search(r'([a-f0-9]{12})', details_text)
                    digest = digest_match.group(1) if digest_match else ''

                    last_updated_match = re.search(r'•\s*(.+ago)', details_text)
                    last_updated = last_updated_match.group(1) if last_updated_match else ''

            if not tag_name:
                continue

            api_tag = tag_name.split(':')[-1] if ':' in tag_name else tag_name

            tag_entry = {
                "tag": tag_name,
                "last_updated": last_updated,
                "size": size.replace('•','').strip(),
                "digest": digest,
                "manifest": None,
                "config": {} # Initialize config dictionary
            }

            try:
                manifest = fetch_manifest(model_name, api_tag)
                if manifest:
                    tag_entry["manifest"] = manifest
                    if manifest.get("config") and manifest["config"].get("digest"):
                        tag_entry["digest"] = manifest["config"]["digest"]
                        config_blob = decode_manifest_config(model_name, tag_entry["digest"])
                        if config_blob:
                            tag_entry["config"] = config_blob
                            # Extract specific parameters from config_blob
                            tag_entry["context_length"] = config_blob.get("parameters", {}).get("context_window")
                            tag_entry["model_type"] = config_blob.get("model_type") # Assuming model_type might be directly in config
                            tag_entry["quantization"] = config_blob.get("quantization") # Assuming quantization might be directly in config
                            tag_entry["base_model"] = config_blob.get("base_model") # Assuming base_model might be directly in config

                    # Extract context_window and input_type from manifest layers (if still present/relevant)
                    for layer in manifest.get("layers", []):
                        layer["mediaType"] = normalize_layer_media_type(layer["mediaType"])
                        if layer.get("annotations"):
                            if "ollama.context_window" in layer["annotations"] and not tag_entry.get("context_length"):
                                tag_entry["context_length"] = layer["annotations"]["ollama.context_window"]
                            if "ollama.input_type" in layer["annotations"] and not tag_entry.get("model_type"):
                                tag_entry["model_type"] = layer["annotations"]["ollama.input_type"]

            except Exception as e:
                log_message(f"Error fetching manifest or decoding config for {api_tag}: {e}", level="ERROR")

            tags_data.append(tag_entry)

    except Exception as e:
        log_message(f"Error scraping tags page for {model_name}: {e}", level="ERROR")
        
    return tags_data

def scrape_details(page, model_name):
    """
    Scrape metadata from a model's main library page.
    Fields captured include description, license, pull counts, architecture, freshness hash, and full README content.
    """
    result = {"name": model_name}
    url = f"https://ollama.com/library/{model_name}"
    try:
        log_message(f"Fetching details page: {url}")
        page.goto(url, wait_until="networkidle", timeout=90000) # Increased timeout
        page.wait_for_timeout(5000) # Give JS more time to render
        page.mouse.wheel(0, 2000) # Simulate more scrolling
        time.sleep(2) # Give time after scroll

        soup = BeautifulSoup(page.content(), "html.parser")

        # Scrape the meta description tag if present
        m = soup.find("meta", {"name": "description"})
        result["description"] = m["content"].strip() if m else ""

        # Attempt to parse license via regex fallback to labeled paragraphs
        lm = re.search(r'licensed under the ([\w\-]+)', page.content(), re.IGNORECASE)
        if lm:
            result["license"] = lm.group(1)
        else:
            lic = soup.find(text=re.compile(r'License', re.IGNORECASE))
            if lic and lic.parent:
                p = lic.parent.find_next("p")
                result["license"] = p.text.strip() if p else ""

        # Extract pull/download count and last-updated timestamp using x-test attributes
        pull_count_span = soup.find("span", attrs={"x-test-pull-count": True})
        if pull_count_span:
            result["pull_count"] = parse_pull_count(pull_count_span.text.strip())
        
        last_updated_span = soup.find("span", attrs={"x-test-updated": True})
        if last_updated_span and last_updated_span.parent and last_updated_span.parent.has_attr('title'):
            result["last_updated"] = last_updated_span.parent['title']
        else:
            result["last_updated"] = last_updated_span.text.strip() if last_updated_span else ""

        # Simple search in the README area for architecture and family info
        prose = soup.find("div", class_="prose")
        result["readme_html"] = str(prose) if prose else ""
        content_txt = prose.get_text(" ") if prose else ""
        m_arch = re.search(r'architecture:\s*([\w\-]+)', content_txt, re.IGNORECASE)
        if m_arch:
            result["architecture"] = m_arch.group(1)
        m_family = re.search(r'family:\s*([\w\-]+)', content_txt, re.IGNORECASE)
        if m_family:
            result["family"] = m_family.group(1)

        # Add a snapshot hash of the current HTML to detect changes
        result["page_hash"] = get_hash(soup.prettify())

        # Extract full README content
        prose_element = soup.find("div", class_="prose")
        if prose_element:
            result["readme_html"] = str(prose_element)
            result["readme_text"] = prose_element.get_text()
        else:
            result["readme_html"] = ""
            result["readme_text"] = ""
    except PlaywrightTimeout as e:
        log_message(f"Timeout on details page for {model_name}: {e}", level="ERROR")
        page.screenshot(path=os.path.join(DEBUG_DIR, f"{model_name}_details_timeout.png"))
        with open(os.path.join(DEBUG_DIR, f"{model_name}_details_timeout.html"), "w", encoding="utf-8") as f:
            f.write(page.content())
    except Exception as e:
        log_message(f"Error scraping details page for {model_name}: {e}", level="ERROR")

    return result

def enrich_model_data(detail):
    """
    Enriches the model data by parsing annotations and README content.
    """
    # Backfill missing annotations from README
    if "ollama.context_window" not in detail.get("annotations", {}) and "readme_text" in detail:
        match = re.search(r'context window(?: of)? (\d+K?)\b', detail["readme_text"], re.IGNORECASE)
        if match:
            if "annotations" not in detail:
                detail["annotations"] = {}
            detail["annotations"]["ollama.context_window"] = match.group(1)
            
    if "ollama.input_type" not in detail.get("annotations", {}) and "readme_text" in detail:
        if re.search(r'\bchat\b', detail["readme_text"], re.IGNORECASE):
            if "annotations" not in detail:
                detail["annotations"] = {}
            detail["annotations"]["ollama.input_type"] = "chat"
        elif re.search(r'\bcode\b', detail["readme_text"], re.IGNORECASE):
            if "annotations" not in detail:
                detail["annotations"] = {}
            detail["annotations"]["ollama.input_type"] = "code"
        elif re.search(r'\btext\b', detail["readme_text"], re.IGNORECASE):
            if "annotations" not in detail:
                detail["annotations"] = {}
            detail["annotations"]["ollama.input_type"] = "text"

    return detail



def scrape_ollama_models_from_web(headless=True, debug_model=None, use_cache=True):
    """
    Orchestrates the scraping flow for Ollama.com specific data:
      1. Launches browser
      2. Fetches list of model names from /library
      3. Iterates each model:
         - scrapes details page
         - fetches manifest from registry API
      4. Writes output to individual JSON files in models/ollama
    """
    if use_cache:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        requests_cache.install_cache(str(CACHE_PATH))

    results = []
    os.makedirs(DEBUG_DIR, exist_ok=True)
    os.makedirs(OLLAMA_MODELS_DIR, exist_ok=True)

    with sync_playwright() as wp:
        browser = wp.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled"])
        page = browser.new_page()
        
        # Capture console messages (JS errors, etc.)
        page.on("console", lambda msg: log_message(f"Browser Console: {msg.text}", level="DEBUG"))

        try:
            log_message("Fetching main library page from Ollama.com")
            page.goto("https://ollama.com/library", wait_until="networkidle", timeout=60000)
            page.wait_for_selector("ul[role=list] > li a", timeout=15000)

            # Parse library index for hrefs
            soup = BeautifulSoup(page.content(), "html.parser")
            items = soup.select("ul[role=list] > li")
            names = [
                i.find("a")["href"].split("/")[-1]
                for i in items
                if i.find("a") and "/library/" in i.find("a")["href"]
            ]
            log_message(f"Found {len(names)} models on Ollama.com")
        except Exception as e:
            log_message(f"Failed to scan Ollama.com library index: {e}", level="ERROR")
            names = []

        # Filter for debug_model if specified
        if debug_model:
            names = [n for n in names if n == debug_model]
            if not names:
                log_message(f"Debug model '{debug_model}' not found in Ollama.com initial list.", level="ERROR")
                return []

        # Loop through each model name
        for i, name in enumerate(names):
            log_message(f"==> Processing Ollama.com model: {name} ({i+1}/{len(names)})", status=f"{i+1}/{len(names)}", phase="ollama_scrape")
            
            model_file_path = os.path.join(OLLAMA_MODELS_DIR, f"{name.replace('/', '_')}.json")
            existing_model_data = {}
            if os.path.exists(model_file_path):
                with open(model_file_path, "r", encoding="utf-8") as f:
                    existing_model_data = json.load(f)

            # First, get the current page hash to check for changes
            current_page_hash = None
            try:
                temp_page = browser.new_page() # Use a new page to avoid interfering with main page
                temp_page.goto(f"https://ollama.com/library/{name}", wait_until="networkidle", timeout=90000)
                temp_soup = BeautifulSoup(temp_page.content(), "html.parser")
                current_page_hash = get_hash(temp_soup.prettify())
                temp_page.close()
            except PlaywrightTimeout as e:
                log_message(f"Timeout getting hash for {name}: {e}", level="ERROR")
                temp_page.close()
                continue # Skip this model if we can't even get the hash
            except Exception as e:
                log_message(f"Error getting hash for {name}: {e}", level="ERROR")
                temp_page.close()
                continue # Skip this model if we can't even get the hash

            detail = {}
            if existing_model_data and existing_model_data.get("page_hash") == current_page_hash:
                log_message(f"Page hash for {name} matches existing data. Skipping detailed scrape.", phase="ollama_scrape")
                detail = existing_model_data
            else:
                log_message(f"Page hash for {name} changed or no existing data. Performing full scrape.", phase="ollama_scrape")
                detail = scrape_details(page, name)
                detail["page_hash"] = current_page_hash # Ensure the new hash is stored

                # Scrape the tags page for version info
                detail["tags"] = scrape_tags_page(page, name)

                # Enrich the model data
                detail = enrich_model_data(detail)

                # Post-process the model data (including quality score)
                detail = post_process_model_data(detail)

            # Save individual model JSON file
            with open(model_file_path, "w", encoding="utf-8") as mf:
                json.dump(detail, mf, indent=2)
            results.append(detail)
            time.sleep(0.3)  # politeness delay

        browser.close()

    log_message(f"Ollama.com scraping complete — {len(results)} models stored in {OLLAMA_MODELS_DIR}", status="COMPLETE", phase="done")

if __name__ == "__main__":
    # Reset log file each trace for clean debugging
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    
    headless_mode = True
    debug_model_name = None
    use_cache = "--no-cache" not in sys.argv

    if "--headless=false" in sys.argv:
        headless_mode = False
    
    # Parse --debug-model argument
    for i, arg in enumerate(sys.argv):
        if arg.startswith("--debug-model="):
            debug_model_name = arg.split("=")[1]
            break

    scrape_ollama_models_from_web(headless=headless_mode, debug_model=debug_model_name, use_cache=use_cache)
