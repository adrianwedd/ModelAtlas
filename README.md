ModelAtlas

A dynamic, enriched intelligence system mapping the foundation model landscape. Trust. Trace. Transform.

⸻

🌐 Overview

ModelAtlas is a modular, agentic system for enriching, auditing, and navigating the expanding universe of large language models (LLMs). It combines:
	•	🔍 Semantic search via CLI (atlas)
	•	🧠 Recursive agent-driven enrichment (RECURSOR-1)
	•	🛡️ Trust scoring & risk heuristics (TrustForge)
	•	📊 Visual dashboards (AtlasView)
	•	🧾 Model lineage inspection (tracepoint)

⸻

📁 File Structure

modelatlas/
├── atlas_cli/             # CLI Tool
├── enrich/                # Enrichment logic (embeddings, heuristics)
├── trustforge/            # Trust score engine
├── recursor/              # Autonomous enrichment agent
├── tracepoint/            # Lineage & provenance debugger
├── dashboards/            # React-based visualizations
├── data/
│   ├── models_raw.json
│   └── models_enriched.json
├── docs/
│   ├── naming.md
│   ├── schema.md
│   └── usage_examples.md
├── ROADMAP.md
├── AGENTS.md
├── tasks.yml
├── README.md
└── atlas.config.json


⸻

🧭 Components

atlas-cli

A developer-friendly interface for semantically searching and filtering enriched models.

TrustForge

Signal fusion engine that assigns model trust scores based on usage, licensing, evals, activity, and provenance.

Recursor

Autonomous enrichment agent. Scrapes metadata, prompts LLMs, normalizes attributes, proposes task.yml changes.

TracePoint

Debugging tool to inspect and trace a model’s enrichment lineage, provenance, risks, and prompt trails.

AtlasView

Interactive dashboard using React/Recharts for architecture, license, size, trust analysis.

⸻

📋 Meta Docs
	•	ROADMAP.md: Vision, milestones, iteration plan
	•	AGENTS.md: Agent specs, roles, loop logic, memory/state
	•	tasks.yml: Canonical taskgraph (schema in comment)
	•	naming.md: Philosophy and mapping of naming conventions to functions

⸻

🧪 Example Commands

# Search enriched models
atlas search "code completion with high trust"

# Inspect trust breakdown for a model
atlas trust-score mistral:7b

# View enrichment lineage and provenance
tracepoint llama3:8b --lineage


⸻

🛠️ Tech Stack
	•	Python (CLI, backend agents)
	•	React + Tailwind + Recharts (dashboard)
	•	Ollama / Hugging Face metadata
	•	JSON as canonical data format
	•	OpenAI / Local LLMs (phi, gemma, deepseek) for enrichment
    •	Github Actions


⸻

🚀 Naming Subsystem

Module	Name	Role
Project	ModelAtlas	Top-level system
Trust Engine	TrustForge	Computes trust scores
Recursive Agent	RECURSOR-1	Enrichment loop agent
CLI	atlas-cli	Entry-point CLI tool
Lineage Debugger	tracepoint	Model enrichment inspection
Dashboard	AtlasView	Visual system overview


⸻

## 🚀 Phase 2 Enhancements

We are actively enhancing ModelAtlas with deeper insights and improved data quality. Key focus areas include:

- **Manifest Enrichment**: Decoding model parameters (context window, quantization, model type) from manifest blobs.
- **Human-Readable Tags**: Capturing clear, human-readable tag names (e.g., `8b-instruct`, `latest`) for better versioning.
- **Data Quality Scoring**: Implementing a completeness score for each model to highlight data gaps and prioritize enrichment efforts.

For a detailed breakdown of Phase 2 objectives and architecture, refer to [docs/PHASE_2_DESIGN.md](docs/PHASE_2_DESIGN.md).

---

Let’s map the modelscape.