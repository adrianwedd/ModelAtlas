## Cycle 4: Strategic Shift to Hugging Face Hub API

**Objective:** Replace brittle web scraping of Ollama.com with a more robust and reliable data acquisition method using the Hugging Face Hub API.

**Rationale:**
*   Web scraping proved highly fragile due to dynamic content, JS rendering, and potential bot mitigation on Ollama.com.
*   Hugging Face Hub provides structured, comprehensive model metadata via an official API, eliminating the need for complex HTML parsing.

**Actions Taken:**
1.  Added `huggingface_hub` to `requirements.txt`.
2.  Created `tools/scrape_hf.py` to leverage `huggingface_hub.list_models` and `api.model_info` for data extraction.
3.  Updated `tasks.yml` to point Task 1 to `tools/scrape_hf.py`.

**Expected Outcome:**
*   More reliable and faster data acquisition.
*   Access to richer, structured metadata (downloads, licenses, tags, benchmarks, etc.) directly from the API.
*   Reduced maintenance overhead due to changes in Ollama.com's UI.

**Next Step:** Execute `tools/scrape_hf.py` to populate `data/models_raw.json`.