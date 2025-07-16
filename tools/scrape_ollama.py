from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import json, sys, re, time, hashlib, os

LOG_FILE = "ollama_scraper.log"     # Log file path for audit & debugging
OUTPUT_FILE = "models_raw.json"     # Output JSON file for scraped models

def log_message(message, level="INFO"):
    """Append a timestamped log entry to LOG_FILE."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] [{level}] {message}\n")

def parse_pull_count(s):
    """Normalize text counts like '1.2M' or '650K' into integer counts."""
    if not s:
        return 0
    s = s.replace("Downloads", "").strip()
    try:
        if "M" in s:
            return int(float(s.replace("M","")) * 1e6)
        if "K" in s:
            return int(float(s.replace("K","")) * 1e3)
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
        page.wait_for_selector("h1", timeout=15000)
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

        # Extract pull/download count and last-updated timestamp
        div = soup.find("div", class_=re.compile(r"text-sm"))
        if div:
            txt = div.get_text(" ").strip()
            result["pull_count"] = parse_pull_count(txt)
            lu = re.search(r'(\d+\s(?:day|week|month|year)s?\sago)', txt)
            if lu:
                result["last_updated"] = lu.group(1)

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
        page.wait_for_selector("ul.divide-y > li", timeout=15000)
        soup = BeautifulSoup(page.content(), "html.parser")

        # Iterate list items representing each quantized variant
        for li in soup.select("ul.divide-y > li"):
            name = li.find("a", class_="group")
            tag_name = name.find("span").text.strip() if name else None
            p = li.find("p", class_=re.compile(r"text-neutral-500"))
            txt = p.get_text(" ") if p else ""
            tags.append({
                "name": tag_name,
                "size": re.search(r'(\d+\.?\d*GB)', txt).group(1) if re.search(r'(\d+\.?\d*GB)', txt) else None,
                "context_window": re.search(r'(\d+K context window)', txt).group(1) if re.search(r'(\d+K context window)', txt) else None,
                "input_type": re.search(r'(Text|Multimodal) input', txt).group(1) if re.search(r'(Text|Multimodal) input', txt) else None,
                "last_updated": re.search(r'\d+\s(?:day|week|month|year)s?\sago', txt).group(0) if re.search(r'\d+\s(?:day|week|month|year)s?\sago', txt) else None,
                "digest": re.search(r'([a-f0-9]{12,})', txt).group(1) if re.search(r'([a-f0-9]{12,})', txt) else None,
            })
    except PlaywrightTimeout as e:
        log_message(f"Timeout on tags page for {model_name}: {e}", level="ERROR")
    except Exception as e:
        log_message(f"Error scraping tags page for {model_name}: {e}", level="ERROR")

    return tags

def run_scraper(headless=True):
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
        browser = wp.chromium.launch(headless=headless)
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

        # Loop through each model name
        for i, name in enumerate(names):
            log_message(f"==> Scraping [{i+1}/{len(names)}]: {name}")
            detail = scrape_details(page, name)
            detail["tags"] = scrape_tags(page, name)
            results.append(detail)
            time.sleep(0.3)  # politeness delay

        browser.close()

    # Save JSON output
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    log_message(f"Scraping complete — {len(results)} models stored in {OUTPUT_FILE}")

if __name__ == "__main__":
    # Reset log file each run for clean debugging
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    head = not ("--headless=false" in sys.argv)
    run_scraper(headless=head)