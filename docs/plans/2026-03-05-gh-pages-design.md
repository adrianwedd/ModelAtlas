# ModelAtlas GH Pages — Design Document

**Date:** 2026-03-05
**Status:** Approved

## Goal

Publish ModelAtlas model intelligence data as a live, beautiful, research-credible catalog at `https://adrianwedd.github.io/ModelAtlas/`. Serves both developers evaluating models and as a portfolio/showcase of the ModelAtlas pipeline.

---

## Architecture

**Approach:** Pure static site — no build step, no npm.

**Files:**
```
site/
  index.html     — single-page app
  style.css      — styles
  app.js         — Alpine.js app logic
```

**Libraries (CDN, no install):**
- [Alpine.js](https://alpinejs.dev/) — reactive search/filter/sort
- [Chart.js](https://www.chartjs.org/) — license donut, trust histogram, top-tags bar chart

**Data source:** `models_enriched.json` is committed to the repo and copied into `site/` at deploy time. Fetched client-side as `./models_enriched.json`. All filtering and sorting runs in-browser (103 models is trivial for JS).

---

## Page Layout

```
┌─────────────────────────────────────────────────────┐
│  MODELATLAS          AI Model Intelligence Catalog  │  header
├───────┬────────┬──────────┬──────────────────────────┤
│  103  │  90%   │   0.57   │  ASR: coming soon        │  hero stats
│models │licensed│avg trust │  (Failure-First)         │
├───────┴────────┴──────────┴──────────────────────────┤
│  [License donut]  [Trust histogram]  [Top tags bar]  │  charts row
├─────────────────────────────────────────────────────┤
│  🔍 Search models...  [License ▾] [Trust ▾] [Sort ▾] │  filter bar
├──────────────────┬────────┬─────────┬───────┬────────┤
│  Name            │ Tags   │ License │ Trust │  ASR   │  table
│  bert-base-...   │ [nlp]  │ apache  │ ●●●○○ │   —    │
│  clip-vit-...    │ [cv]   │ mit     │ ●●●●○ │   —    │
│  deepseek-r1     │ [llm]  │ other   │ ●●●○○ │   —    │
└──────────────────┴────────┴─────────┴───────┴────────┘
```

---

## Components

### Hero stat chips
Four chips in a row: model count, licensed %, avg trust score, ASR status.
ASR chip has dashed border + muted color — reads as *intentionally absent*, not broken.

### Charts (3)
1. **License donut** — apache-2.0 vs mit vs other vs unlicensed
2. **Trust score histogram** — distribution across 0.0–1.0 buckets (currently 0.4–0.8)
3. **Top tags bar** — horizontal, top 10 tags by frequency (filtered to meaningful ones, strip `region:us` etc.)

### Filter bar
- Text search (name + tags, debounced 150ms)
- License dropdown (All / Apache-2.0 / MIT / Restrictive / Unlicensed)
- Trust score range (slider: 0.0–1.0)
- Sort: by name / trust score / last updated

### Model table
Columns: **Name** (monospace, links to HF/Ollama) | **Tags** (top 3 as chips) | **License** (colored badge) | **Trust** (5-dot indicator) | **ASR** (dashed `—` now, red number when Failure-First data lands)

No pagination — all rows rendered. If count exceeds ~500, add virtual scrolling as a separate sprint.

---

## Visual Design

**Theme:** Dark, research-tool aesthetic.

| Token | Value |
|-------|-------|
| Background | `#0d1117` (GitHub dark) |
| Surface | `#161b22` |
| Border | `#30363d` |
| Text | `#e6edf3` |
| Muted | `#7d8590` |
| Trust high | `#3fb950` (green) |
| Trust mid | `#d29922` (amber) |
| Trust low | `#f85149` (red) |
| ASR pending | `#484f58` (grayed) |

**Typography:** `system-ui` for body, `font-mono` for model names and score values.

**License badges:** Small colored chips — `apache-2.0` green, `mit` blue, restrictive amber, unknown gray.

---

## ASR Integration Slot

The ASR column is present in the table from day one but visually inactive:
- All cells show `—` with color `#484f58`
- Column header has a `ⓘ` tooltip: *"Attack Success Rate from empirical adversarial benchmarks (source: Failure-First). Data pending."*
- Hero stat chip: *"ASR: coming soon"* with dashed border

When Failure-First data lands (Sprint N), populating the 25 overlapping models requires only adding `asr_score` to their entries in `models_enriched.json`. No UI change needed — the table reads the field and renders the value in red if present.

---

## CI/Deployment

**New file:** `.github/workflows/pages.yml`

**Trigger:** Push to `main` (any file — always redeploys on data change)

**Steps:**
1. `actions/checkout`
2. Copy `models_enriched.json` → `site/models_enriched.json`
3. `actions/upload-pages-artifact` with `site/` as path
4. `actions/deploy-pages`

**One-time manual step:** Repo Settings → Pages → Source: GitHub Actions.

**Existing CI unchanged.** `ci.yml` continues to build Sphinx docs as an artifact.

---

## Data Flow

```
pipeline run (local)
        │
        ▼
models_enriched.json  ←── updated, committed, pushed
        │
        ▼
pages.yml workflow
        │
        ▼
site/ + models_enriched.json → GH Pages
        │
        ▼
https://adrianwedd.github.io/ModelAtlas/
  Alpine.js fetches ./models_enriched.json
  All search/filter/sort in browser
```

---

## Out of Scope

- Per-model detail pages (needs build step — revisit if catalog grows)
- Sphinx docs publishing (separate concern, existing CI artifact is sufficient)
- Real-time pipeline trigger from CI (pipeline hits live APIs, needs secrets, not suitable for CI automation)
- Failure-First ASR data integration (Sprint 7)
- `generate_visuals.py` matplotlib charts (separate local tool, not site)
