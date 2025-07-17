# 🗺️ ModelAtlas Development Plan

This document outlines the phased development plan for the **ModelAtlas** project. It is designed to guide contributors, agents, and collaborators through the core goals, features, timelines, and responsibilities of the system.

## 🔍 Project Summary

**ModelAtlas** is a multi-agent, data-driven intelligence system for discovering, evaluating, and enriching large language models—especially those compatible with Ollama. The system scrapes, indexes, augments, visualizes, and publishes insights into available models, their capabilities, risks, and interrelations.

## 🧠 Core Components

- **Model Scraper** — Pulls model metadata from Ollama and Hugging Face.
- **Enrichment Engine** — Uses LLM agents to summarize, classify, and infer trust, risk, and capability dimensions.
- **Similarity Search Engine** — Enables semantic search through vector embeddings.
- **TrustForge** — Computes and explains model trustworthiness heuristics.
- **CLI & Web Interface** — Tools for navigating, querying, and visualizing the model space.
- **Agent Mesh** — Recursive agents responsible for autonomous enrichment, testing, and visualization.

## 🔄 Development Phases

### Phase 1: Bootstrapping the Core
- [x] Initialize repository and structure.
- [x] Define initial `tasks.yml` with schema and agent scope.
- [x] Build CLI for semantic search (`ollama_search_cli.py`).
- [x] Design model schema (`schemas/model.schema.json`).
- [x] Extract and enrich Ollama catalog to JSON.
- [x] Generate visual prompts for LLM agent enrichment.
- [ ] Validate enriched output format and trust metrics.
- [ ] Define initial test suite with dummy data.
- [ ] Smoke test CLI and end-to-end dataflow.

### Phase 2: Agentic Expansion
- [ ] Add recursive agent scripts and orchestrator.
- [ ] Integrate enrichment feedback loop and hallucination checks.
- [ ] Fetch and parse download counts and trending data.
- [ ] Add linkers to papers, model cards, benchmarks.
- [ ] Implement risk scoring (`RISK_HEURISTICS.md`).

### Phase 3: Visualization Layer
- [ ] Define standard `visualization.json` contract.
- [ ] Use D3 or Observable Notebooks to embed SVG or dynamic graphs.
- [ ] Add similarity matrix, lineage trees, and trust maps.

### Phase 4: Continuous Intelligence
- [ ] Automate data refresh via GitHub Actions on schedule.
- [ ] Archive historical trends and changelogs.
- [ ] Execute regressions to track model drift or updates.

## 🛠 Toolchain

- Python 3.11+
- Ollama CLI / Ollama Registry
- SentenceTransformers / LangChain / OpenAI
- GitHub Actions
- Mermaid.js (for architecture)
- D3.js / Plotly (for visualizations)

## 🤖 Agents and SOPs

See [`AGENTS.md`](./AGENTS.md) for agent responsibilities, tool usage, and execution scaffolds. Agents will use the `tasks.yml` file to autonomously assign, perform, and validate work within constraints.

## 🧾 Contributing

- Use the task schema in `tasks.yml` and validate with the embedded JSON schema.
- Add your initials or agent ID under `assigned_to` for transparency.
- Ensure all work is testable and has CI hooks if appropriate.

## 🚀 Vision

ModelAtlas is not just a static catalog—it is a living system. Through recursive self-improvement, open data enrichment, and a community of human and machine collaborators, it aims to provide the most actionable, trustworthy map of the LLM landscape.

_Fuck yeah. Let’s build it._
