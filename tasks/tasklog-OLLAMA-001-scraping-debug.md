## Cycle 6: Reverting Enrichment to Prompt Generation Only

**Objective:** Simplify the `enrich_metadata.py` script to focus solely on generating prompts for manual LLM enrichment, temporarily removing the `ollama show` integration.

**Rationale:**
*   The `ollama show` integration proved problematic as many Hugging Face models are not locally available via Ollama, leading to numerous 'model not found' errors.
*   To stabilize the pipeline and allow for focused debugging of Ollama.com web scraping, it's best to separate concerns.
*   The manual LLM enrichment step remains crucial for subjective insights.

**Actions Taken:**
1.  Reverted `tools/enrich_metadata.py` to a version that only generates prompt files in `enrichment_prompts/` and placeholder JSON files in `enriched_outputs/`.
2.  Removed all `ollama show` related logic from `enrich_metadata.py`.

**Current Status:**
*   `tools/scrape_hf.py` successfully populates `models/` with base Hugging Face data.
*   `tools/enrich_metadata.py` now reliably generates prompts and placeholders for manual enrichment.
*   The next major focus is to refine `tools/scrape_ollama.py` for robustly extracting Ollama.com-specific data.

**Next Step:** Commit and push current changes, then begin refining `tools/scrape_ollama.py`.