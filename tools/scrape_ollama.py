from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import json, sys, re, time, hashlib, os
import requests # Added requests import

LOG_FILE = "ollama_scraper.log"     # Log file path for audit & debugging
OLLAMA_MODELS_DIR = os.path.join("models", "ollama")
DEBUG_DIR = "ollama_debug_dumps"

def log_message(message, level="INFO", status=None, phase=None):
    """Append a timestamped log entry to LOG_FILE, with optional status and phase markers."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    status_str = f"[{status}]" if status else ""
    phase_str = f"[{phase}]" if phase else ""
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] [{level}]{phase_str}{status_str} {message}\n")

def parse_pull_count(s):
    """Normalize text counts like '1.2M' or '650K' into integer counts."""
    if not s:
        return 0
    s = s.replace("Pulls", "").strip()
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

def scrape_details(page, model_name):
    """
    Scrape metadata from a model's main library page.
    Fields captured include description, license, pull counts, architecture and freshness hash.
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
        content_txt = prose.get_text(" ") if prose else ""
        m_arch = re.search(r'architecture:\s*([\w\-]+)', content_txt, re.IGNORECASE)
        if m_arch:
            result["architecture"] = m_arch.group(1)
        m_family = re.search(r'family:\s*([\w\-]+)', content_txt, re.IGNORECASE)
        if m_family:
            result["family"] = m_family.group(1)

        # Add a snapshot hash of the current HTML to detect changes
        result["page_hash"] = get_hash(soup.prettify())

    except PlaywrightTimeout as e:
        log_message(f"Timeout on details page for {model_name}: {e}", level="ERROR")
        page.screenshot(path=os.path.join(DEBUG_DIR, f"{model_name}_details_timeout.png"))
        with open(os.path.join(DEBUG_DIR, f"{model_name}_details_timeout.html"), "w", encoding="utf-8") as f:
            f.write(page.content())
    except Exception as e:
        log_message(f"Error scraping details page for {model_name}: {e}", level="ERROR")

    return result

def scrape_ollama_models_from_web(headless=True, debug_model=None):
    """
    Orchestrates the scraping flow for Ollama.com specific data:
      1. Launches browser
      2. Fetches list of model names from /library
      3. Iterates each model:
         - scrapes details page
         - fetches manifest from registry API
      4. Writes output to individual JSON files in models/ollama
    """
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
            
            detail = scrape_details(page, name)
            
            # Fetch manifest for tags and other structured data
            manifest = fetch_manifest(name)
            if manifest:
                tags_data = []
                for layer in manifest.get("layers", []):
                    tag_entry = {
                        "name": layer.get("mediaType", "").split(":")[-1], # Extract tag name from mediaType
                        "digest": layer.get("digest", ""),
                        "size": f"{round(layer.get("size", 0) / (1024*1024*1024), 2)}GB" if layer.get("size") else None, # Convert bytes to GB
                        "media_type": layer.get("mediaType", ""),
                        "annotations": layer.get("annotations", {})
                    }
                    # Attempt to extract context window and input type from annotations or mediaType
                    if "annotations" in layer and layer["annotations"]:
                        tag_entry["context_window"] = layer["annotations"].get("ollama.context_window")
                        tag_entry["input_type"] = layer["annotations"].get("ollama.input_type")
                        tag_entry["last_updated"] = layer["annotations"].get("ollama.last_modified")
                    
                    tags_data.append(tag_entry)
                detail["tags"] = tags_data
            else:
                detail["tags"] = [] # No manifest found

            # Save individual model JSON file
            model_file_path = os.path.join(OLLAMA_MODELS_DIR, f"{name.replace('/', '_')}.json")
            with open(model_file_path, "w") as mf:
                json.dump(detail, mf, indent=2)
            results.append(detail)
            time.sleep(0.3)  # politeness delay

        browser.close()

    log_message(f"Ollama.com scraping complete — {len(results)} models stored in {OLLAMA_MODELS_DIR}", status="COMPLETE", phase="done")

if __name__ == "__main__":
    # Reset log file each run for clean debugging
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    
    headless_mode = True
    debug_model_name = None

    if "--headless=false" in sys.argv:
        headless_mode = False
    
    # Parse --debug-model argument
    for i, arg in enumerate(sys.argv):
        if arg.startswith("--debug-model="):
            debug_model_name = arg.split("=")[1]
            break

    scrape_ollama_models_from_web(headless=headless_mode, debug_model=debug_model_name)
