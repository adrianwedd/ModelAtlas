
## Cycle 7: Hybrid Scraping Strategy (Hugging Face API + Ollama Registry API)

**Objective:** Implement a robust, multi-phase scraping strategy:
1.  Use Hugging Face Hub API for primary model metadata.
2.  Use Ollama.com web scraping (with Playwright) for unique Ollama.com data (e.g., run commands, specific descriptions).
3.  Use Ollama Registry API for detailed tag/variant information (digest, size, context, modality, release info).

**Rationale:**
*   Hugging Face API provides reliable, structured core model data.
*   Ollama.com web scraping is necessary for data unique to their website (e.g., `ollama run` commands, specific UI-driven descriptions).
*   Ollama Registry API provides highly structured and reliable variant metadata, avoiding brittle DOM parsing of `/tags` pages.

**Actions Taken:**
1.  Modified `tools/scrape_hf.py` to save individual model JSON files to `models/huggingface/`.
2.  Modified `tools/scrape_ollama.py` to:
    *   Save individual model JSON files to `models/ollama/`.
    *   Implement `fetch_manifest` function using `requests` to query Ollama Registry API for tag details.
    *   Integrate `fetch_manifest` to populate `tags` data for Ollama.com models.
    *   Enhanced debugging in `scrape_ollama.py` with screenshot capture, HTML saving on failures, increased timeouts, more scrolling, and console logging.
3.  Updated `tasks.yml` to reflect the two-step scraping process (Task 1 for HF, Task 1.1 for Ollama.com).

**Current Status:**
*   The scraping pipeline is now designed to leverage the strengths of both Hugging Face API and Ollama Registry API, with Playwright used only for Ollama.com-specific web content.
*   Debugging capabilities for Ollama.com scraping are significantly enhanced.

**Next Step:** Execute `python tools/scrape_hf.py` (Task 1), then `python tools/scrape_ollama.py` (Task 1.1).
