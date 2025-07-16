# 📊 Download Metrics Integration

## 🎯 Goal
Incorporate real-time or regularly updated download statistics into the enrichment and trust-scoring system...

## Ollama
- Extracted via DOM from the tile element (`.model-downloads`)
- Normalize to integers (e.g. "1.3M" → 1_300_000)...

## HuggingFace
- Query using: https://huggingface.co/api/models/{model_name}
- Parse and enrich with fallback caching...