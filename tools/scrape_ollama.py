from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import json, sys, re, time, hashlib, os

LOG_FILE = "ollama_scraper.log"     # Log file path for audit & debugging
OUTPUT_FILE = "models_raw.json"     # Output JSON file for scraped models

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

def scrape_details(page, model_name):
    """
    Scrape metadata from a model's main library page.
    Fields captured include description, license, pull counts, architecture and freshness hash.
    """
    result = {"name": model_name}
    url = f"https://ollama.com/library/{model_name}"
    try:
        log_message(f"Fetching details page: {url}")
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000) # Give JS time to render
        page.mouse.wheel(0, 1000) # Simulate scroll
        time.sleep(1) # Give time after scroll

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
    except Exception as e:
        log_message(f"Error scraping details page for {model_name}: {e}", level="ERROR")

    return result

def scrape_tags(page, model_name):
    """
    Scrape tag-variant metadata from the '/tags' sub-page.
    Captures variant id, size, context window, input type, update age, and blob digest.
    """
    tags = []
    url = f"https://ollama.com/library/{model_name}/tags"
    try:
        log_message(f"Fetching tags page: {url}")
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000) # Give JS time to render
        page.mouse.wheel(0, 1000) # Simulate scroll
        time.sleep(1) # Give time after scroll

        soup = BeautifulSoup(page.content(), "html.parser")

        # Iterate list items representing each quantized variant
        for li in soup.select("ul.divide-y > li"):
            tag_data = {}
            name_element = li.find("a", class_="group")
            if name_element:
                tag_data["name"] = name_element.find("span").text.strip()
            
            # Extracting details from the p.text-neutral-500 element
            info_p = li.find("p", class_=re.compile(r"text-neutral-500"))
            if info_p:
                text_content = info_p.get_text(separator=' ', strip=True)
                
                # Digest is in a span with class font-mono
                digest_span = info_p.find("span", class_="font-mono")
                tag_data["digest"] = digest_span.text.strip() if digest_span else None

                # Extracting other details using more specific regexes on the full text
                size_match = re.search(r'(\d+\.?\d*GB)', text_content)
                tag_data["size"] = size_match.group(1) if size_match else None

                context_match = re.search(r'(\d+K context window)', text_content)
                tag_data["context_window"] = context_match.group(1) if context_match else None

                input_match = re.search(r'(Text|Multimodal) input', text_content)
                tag_data["input_type"] = input_match.group(1) if input_match else None

                updated_match = re.search(r'(\d+\s(?:day|week|month|year)s?\sago)', text_content)
                tag_data["last_updated"] = updated_match.group(1) if updated_match else None

            tags.append(tag_data)
    except PlaywrightTimeout as e:
        log_message(f"Timeout on tags page for {model_name}: {e}", level="ERROR")
    except Exception as e:
        log_message(f"Error scraping tags page for {model_name}: {e}", level="ERROR")

    return tags

def run_scraper(headless=True, debug_model=None):
    """
    Orchestrates the scraping flow:
      1. Launches browser
      2. Fetches list of model names from /library
      3. Iterates each model:
         - scrapes details page
         - scrapes tag variants
      4. Writes output to JSON
    """
    results = []
    with sync_playwright() as wp:
        browser = wp.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled"])
        page = browser.new_page()
        try:
            log_message("Fetching main library page")
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
            log_message(f"Found {len(names)} models")
        except Exception as e:
            log_message(f"Failed to scan library index: {e}", level="ERROR")
            names = []

        # Filter for debug_model if specified
        if debug_model:
            names = [n for n in names if n == debug_model]
            if not names:
                log_message(f"Debug model '{debug_model}' not found in initial list.", level="ERROR")
                return []

        # Loop through each model name
        for i, name in enumerate(names):
            log_message(f"==> Scraping [{i+1}/{len(names)}]: {name}", status=f"{i+1}/{len(names)}", phase="scrape")
            detail = scrape_details(page, name)
            detail["tags"] = scrape_tags(page, name)
            # Save individual model JSON file
            model_output_dir = "models"
            os.makedirs(model_output_dir, exist_ok=True)
            model_file_path = os.path.join(model_output_dir, f"{name}.json")
            with open(model_file_path, "w") as mf:
                json.dump(detail, mf, indent=2)
            results.append(detail)
            time.sleep(0.3)  # politeness delay

        browser.close()

    # Save JSON output
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    log_message(f"Scraping complete — {len(results)} models stored in {OUTPUT_FILE}", status="COMPLETE", phase="done")

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

    run_scraper(headless=headless_mode, debug_model=debug_model_name)
