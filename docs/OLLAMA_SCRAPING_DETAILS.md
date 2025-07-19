# Ollama Library Data Extraction

Granularity, God‑Mode Logging, and Recursive Agent Intelligence

 1. Search Page (/library?q=deepseek&sort=popular)

URL template:

https://ollama.com/library?q=<query>&sort=<sort_order>

Structure & Extracted Data
•Model list container – each result is a card.
•Per-card fields:
•id: "deepseek-r1"
•name: "DeepSeek‑R1"
•description tagline
•downloads: integer
•tags: array (capabilities, size labels)
•updated_at: human‑friendly timestamp
•url: link to model detail

JSON Schema for Output

{
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id","name","description","downloads","tags","updated_at","url"],
    "properties": {
      "id": {"type": "string"},
      "name": {"type": "string"},
      "description": {"type": "string"},
      "downloads": {"type": "integer"},
      "tags": {"type": "array","items":{"type":"string"}},
      "updated_at": {"type":"string"},
      "url": {"type":"string","format":"uri"}
    }
  }
}

Agent & Logging Notes
•Fetch logs: fetched_url, timestamp, status_int, headers.
•Parse logs: micro‑detail per model extracted.
•URL logging: includes query params for reproducibility.

⸻

 2. Library Root Page (/library/{model})

Example:

https://ollama.com/library/deepseek-r1

Structure & Extracted Data
•Header: name, tagline, downloads, updated_at, execute_command, license_text.
•Variants table:
•variant_id, size, context_window, input_type, last_updated_variant
•readme_content: full markdown description
•Optional fields: benchmarks_claims, architecture_family, github_link, paper_link, compatibility_notes

JSON Schema

{
  "type": "object",
  "required": ["name","description","downloads","updated_at","license_text","execute_command","variants_overview","readme_content"],
  "properties": {
    "name": {"type":"string"},
    "description": {"type":"string"},
    "downloads": {"type":"integer"},
    "updated_at": {"type":"string"},
    "license_text": {"type":"string"},
    "execute_command": {"type":"string"},
    "variants_overview": {
      "type":"array",
      "items":{
        "type":"object",
        "required":["variant_id","size","context_window","input_type","last_updated_variant"],
        "properties":{
          "variant_id":{"type":"string"},
          "size":{"type":"string"},
          "context_window":{"type":"string"},
          "input_type":{"type":"string"},
          "last_updated_variant":{"type":"string"}
        }
      }
    },
    "readme_content":{"type":"string"},
    "architecture_family":{"type":"string"},
    "benchmarks_claims":{"type":"array","items":{"type":"string"}},
    "github_link":{"type":"string","format":"uri"},
    "paper_link":{"type":"string","format":"uri"},
    "compatibility_notes":{"type":"string"}
  }
}

Agent & Logging Notes
•Header fetch logs micro‑steps: header→variants→README.
•License parsing → SPDX assignment and logging.
•Change detection → compare old vs. new license hashes or variant sets.

⸻

 3. Variant Metadata Blob (/library/{model}:{variant}/blobs/{hash})

Example:

https://ollama.com/library/deepseek-r1:1.5b/blobs/aABD...

Structure & Extracted Data
•JSON blob includes:
•general: { architecture, parameters, quantization, file_size_bytes }
•tokenizer_attributes, model_config, context_length

JSON Schema

{
  "type":"object",
  "required":["model_name","variant_tag","blob_hash","general","model_config"],
  "properties":{
    "model_name":{"type":"string"},
    "variant_tag":{"type":"string"},
    "blob_hash":{"type":"string","pattern":"^[a-f0-9]{12,}$"},
    "general":{
      "type":"object",
      "required":["architecture","parameters","quantization","file_size_bytes"],
      "properties":{
        "architecture":{"type":"string"},
        "parameters":{"type":"number"},
        "quantization":{"type":"string"},
        "file_size_bytes":{"type":"integer"}
      }
    },
    "tokenizer_attributes":{"type":"object","additionalProperties":true},
    "model_config":{"type":"object","additionalProperties":true},
    "context_length":{"type":"integer"}
  }
}

Agent & Logging Notes
•Checksum each blob → detect duplicates or updates.
•Full dump in logs for God‑mode review.
•Tagging by architecture families, quantization, context.

⸻

 4. License Blob

Example:

.../deepseek-r1/blobs/6e4c38e1172f

Extracted Data
•model_name, license_hash, filename, content, size_bytes
•oss_compatibility_verdict (derived by TrustForge)

JSON Schema

{
  "type":"object",
  "required":["model_name","license_hash","filename","content","size_bytes"],
  "properties":{
    "model_name":{"type":"string"},
    "license_hash":{"type":"string","pattern":"^[a-f0-9]{12,}$"},
    "filename":{"type":"string"},
    "content":{"type":"string"},
    "size_bytes":{"type":"integer"},
    "oss_compatibility_verdict":{"type":"string"}
  }
}

Agent & Logging Notes
•SHA256 log, license content dump.
•Verdict inference using SPDX + heuristics.

⸻

 5. Template / Prompt Blob

Example:

.../deepseek-r1/blobs/c5ad996bda6e

Extracted Data
•model_name, template_hash, filename, content, placeholders array

JSON Schema

{
  "type":"object",
  "required":["model_name","template_hash","filename","content","placeholders"],
  "properties":{
    "model_name":{"type":"string"},
    "template_hash":{"type":"string","pattern":"^[a-f0-9]{12,}$"},
    "filename":{"type":"string"},
    "content":{"type":"string"},
    "placeholders":{"type":"array","items":{"type":"string"}}
  }
}

Agent & Logging Notes
•Template logging ensures prompt reproducibility.
•Placeholder tracking helps map template usage across models.

⸻

 6. MoE or Specialized Variants (/library/{model}-v3)

Includes all fields from Library Root pages, with extra:
•github_link, paper_link, compatibility_notes, variant sizes (large like 400GB)

Schema Enhancements
•Add the necessary URI fields and highlight compatibility notes in variants.

⸻

 Agent & Logging Strategy

Granular fetch logging:
•Endpoint, timestamp, HTTP code, payload size.

Parsing logs:
•Each field extracted is logged individually.
•Diffs tracked with old vs. new data hashes.

God‑Mode dumps:
•Raw blobs saved under agentlogs/recursor/<model>/<step>.json

Recursive agent loop:
1.Scan /library?sort=recent
2.Fetch model root; parse
3.Recursively fetch variant blobs, license, prompts
4.Log micro-steps, produce JSON
5.Update tasks.yml with status and next steps
6.TrustForge consumes parsed results

⸻

✅ Next Agent Tasks
1.scrape_ollama.py: implement full-scrape flow & logging
2.schemas/library_*.schema.json: finalize schemas for each page type
3.AGENTS.md: outline the fetch→parse→log pattern
4.tasks.yml: add per-model+step tasks (see Plan.md for full list)
5.Execute & validate against live Ollama pages
6.Then: move to enrichment (TrustForge + RECURSOR loop)
