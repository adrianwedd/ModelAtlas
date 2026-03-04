# Sprint 6: API & Config Fixes

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix two HIGH serve_api bugs (wrong data path, missing error handling), one MEDIUM stale-global bug, and two MEDIUM hardcoded-path issues found in QA Round 6.

**Architecture:** Point fixes only. TDD. No new abstractions.

**Tech Stack:** Python 3.11+, pytest, Pydantic v2, FastAPI

**GH Issues closed by this sprint:** #168, #169, #170, #171, #172

---

## Issues Fixed

| # | Sev | File | Bug | GH Issue |
|---|-----|------|-----|---------|
| 1 | HIGH | `tools/serve_api.py:16` | Hardcoded `models_similar.json` path — file doesn't exist, API silently returns empty | #168 |
| 2 | HIGH | `tools/serve_api.py:25-26` | Missing JSONDecodeError handler in `load_models_data` — crashes on corrupted file | #169 |
| 3 | MEDIUM | `tools/serve_api.py:29` | Module-level `models_data = load_models_data()` never refreshed — stale state | #170 |
| 4 | MEDIUM | `generate_visuals.py:12` | Hardcoded relative `"models_enriched.json"` path instead of `settings.OUTPUT_FILE` | #171 |
| 5 | MEDIUM | `tools/enrich_metadata.py:11-13` | Hardcoded `MODELS_DIR`, `PROMPTS_DIR`, `ENRICHED_OUTPUTS_DIR` instead of `settings` | #172 |

---

### Task 1: Fix serve_api.py wrong data path + missing JSONDecodeError (Issues #168 + #169)

**Files:**
- Modify: `tools/serve_api.py` (lines 15-26)
- Test: `tests/test_serve_api.py` (extend — file already exists)

**Root cause:** Line 16 points at `data/models_similar.json`, a file that does not exist. The correct catalog is `models_enriched.json`, accessible via `settings.PROJECT_ROOT / settings.OUTPUT_FILE`. Lines 25-26 call `json.load` with no error handling — a corrupted file raises `json.JSONDecodeError` and crashes the entire API process.

**Step 1: Write failing tests**

Add to `tests/test_serve_api.py`:

```python
def test_load_models_data_returns_empty_on_nonexistent_file(tmp_path):
    """load_models_data must return [] if data file doesn't exist."""
    import tools.serve_api as api
    original = api.MODELS_DATA_PATH
    api.MODELS_DATA_PATH = tmp_path / "nonexistent.json"
    try:
        result = api.load_models_data()
        assert result == []
    finally:
        api.MODELS_DATA_PATH = original


def test_load_models_data_returns_empty_on_corrupted_json(tmp_path):
    """load_models_data must return [] on corrupted JSON, not raise."""
    import tools.serve_api as api
    bad = tmp_path / "bad.json"
    bad.write_text("{corrupted")
    original = api.MODELS_DATA_PATH
    api.MODELS_DATA_PATH = bad
    try:
        result = api.load_models_data()
        assert result == []
    finally:
        api.MODELS_DATA_PATH = original
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_serve_api.py::test_load_models_data_returns_empty_on_nonexistent_file tests/test_serve_api.py::test_load_models_data_returns_empty_on_corrupted_json -v
```

Expected: `test_load_models_data_returns_empty_on_nonexistent_file` FAILS (`AttributeError: module 'tools.serve_api' has no attribute 'MODELS_DATA_PATH'`). `test_load_models_data_returns_empty_on_corrupted_json` FAILS (`json.JSONDecodeError` raised, not caught).

**Step 3: Apply fix**

In `tools/serve_api.py`, make these changes:

1. Add `import logging` to the stdlib imports at the top.

2. Replace the old constant and `load_models_data` function:

```python
# BEFORE
# Assuming models_similar.json is in the data directory
MODELS_SIMILAR_PATH = settings.PROJECT_ROOT / "data" / "models_similar.json"

app = FastAPI(title="ModelAtlas API")


# Load models data
def load_models_data():
    if not MODELS_SIMILAR_PATH.exists():
        return []
    with open(MODELS_SIMILAR_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# AFTER
logger = logging.getLogger(__name__)

MODELS_DATA_PATH = settings.PROJECT_ROOT / settings.OUTPUT_FILE

app = FastAPI(title="ModelAtlas API")


# Load models data
def load_models_data():
    if not MODELS_DATA_PATH.exists():
        return []
    try:
        with open(MODELS_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error("Catalog JSON is corrupted: %s", e)
        return []
```

**Step 4: Run tests**

```bash
pytest tests/test_serve_api.py -v
pytest --tb=short -q
```

Expected: all PASS.

**Step 5: Commit**

```bash
git add tools/serve_api.py tests/test_serve_api.py
git commit -m "fix: use settings.OUTPUT_FILE for API data path; add JSONDecodeError handler in load_models_data"
```

---

### Task 2: Fix serve_api.py stale module-level global (Issue #170)

**Files:**
- Modify: `tools/serve_api.py` (line 29 and three route handlers)
- Test: `tests/test_serve_api.py` (add new test; update existing fixture)

**Root cause:** `models_data = load_models_data()` on line 29 is evaluated once at import time. Any update to `models_enriched.json` after the process starts is never reflected. Removing the global and calling `load_models_data()` inside each route handler ensures fresh data on every request.

**Important:** The existing `client` fixture in `tests/test_serve_api.py` sets `api_module.models_data = FAKE_MODELS` after import. Once the global is removed, that assignment is a no-op and existing tests will break. The fixture must be updated to rely solely on the existing `patch("tools.serve_api.load_models_data", return_value=FAKE_MODELS)` mock.

**Step 1: Write failing test**

Add to `tests/test_serve_api.py`:

```python
def test_get_all_models_reflects_file_changes(tmp_path):
    """get_all_models must load fresh data on each call, not use cached global."""
    import json as json_mod
    import tools.serve_api as api
    from fastapi.testclient import TestClient

    data_file = tmp_path / "models.json"
    data_file.write_text(json_mod.dumps([{"name": "bert"}]))

    original = api.MODELS_DATA_PATH
    api.MODELS_DATA_PATH = data_file
    try:
        client = TestClient(api.app)
        resp1 = client.get("/models")
        assert len(resp1.json()) == 1

        # Simulate file update between requests
        data_file.write_text(json_mod.dumps([{"name": "bert"}, {"name": "gpt2"}]))
        resp2 = client.get("/models")
        assert len(resp2.json()) == 2, "API must reflect updated file on second request"
    finally:
        api.MODELS_DATA_PATH = original
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_serve_api.py::test_get_all_models_reflects_file_changes -v
```

Expected: FAIL — module-level `models_data` is stale, `resp2` still returns 1 item.

**Step 3: Apply fix**

In `tools/serve_api.py`:

1. Delete line 29: `models_data = load_models_data()`

2. Update all three route handlers to call `load_models_data()` directly:

```python
# BEFORE
models_data = load_models_data()


@app.get("/models", response_model=List[Model])
async def get_all_models():
    return models_data


@app.get("/models/{model_name}", response_model=Model)
async def get_model_by_name(model_name: str):
    for model in models_data:
        if model["name"] == model_name:
            return model
    raise HTTPException(status_code=404, detail="Model not found")


@app.get("/models/{model_name}/similar", response_model=List[dict])
async def get_similar_models(model_name: str):
    for model in models_data:
        if model["name"] == model_name:
            return model.get("similar_models", [])
    raise HTTPException(status_code=404, detail="Model not found")

# AFTER (global removed, each handler calls load_models_data() directly)
@app.get("/models", response_model=List[Model])
async def get_all_models():
    return load_models_data()


@app.get("/models/{model_name}", response_model=Model)
async def get_model_by_name(model_name: str):
    for model in load_models_data():
        if model["name"] == model_name:
            return model
    raise HTTPException(status_code=404, detail="Model not found")


@app.get("/models/{model_name}/similar", response_model=List[dict])
async def get_similar_models(model_name: str):
    for model in load_models_data():
        if model["name"] == model_name:
            return model.get("similar_models", [])
    raise HTTPException(status_code=404, detail="Model not found")
```

3. Update the `client` fixture in `tests/test_serve_api.py` — remove the now-broken `api_module.models_data = FAKE_MODELS` line:

```python
# BEFORE
@pytest.fixture
def client():
    with patch("tools.serve_api.load_models_data", return_value=FAKE_MODELS):
        import tools.serve_api as api_module
        api_module.models_data = FAKE_MODELS
        from fastapi.testclient import TestClient
        yield TestClient(api_module.app)

# AFTER
@pytest.fixture
def client():
    with patch("tools.serve_api.load_models_data", return_value=FAKE_MODELS):
        import tools.serve_api as api_module
        from fastapi.testclient import TestClient
        yield TestClient(api_module.app)
```

**Step 4: Run tests**

```bash
pytest tests/test_serve_api.py -v
pytest --tb=short -q
```

Expected: all PASS, including the new freshness test and all pre-existing route tests.

**Step 5: Commit**

```bash
git add tools/serve_api.py tests/test_serve_api.py
git commit -m "fix: remove stale module-level models_data global; load fresh data per request in serve_api"
```

---

### Task 3: Fix generate_visuals.py hardcoded path (Issue #171)

**Files:**
- Modify: `generate_visuals.py` (line 12)
- Test: `tests/test_generate_visuals.py` (create — does not exist yet)

**Root cause:** `data_path = "models_enriched.json"` on line 12 is a relative path that resolves to whatever the process's working directory is at runtime. It must use `settings.PROJECT_ROOT / settings.OUTPUT_FILE` to be location-independent. `generate_readme.py` was fixed in Sprint 5 but this file was missed.

**Step 1: Write failing test**

Create `tests/test_generate_visuals.py`:

```python
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def test_generate_visuals_uses_settings_output_file():
    """generate_visuals.main must not hardcode 'models_enriched.json' relative path."""
    import inspect
    import generate_visuals
    src = inspect.getsource(generate_visuals.main)
    assert '"models_enriched.json"' not in src, (
        "generate_visuals must use settings.PROJECT_ROOT / settings.OUTPUT_FILE, "
        "not the hardcoded string 'models_enriched.json'"
    )
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_generate_visuals.py::test_generate_visuals_uses_settings_output_file -v
```

Expected: FAIL — `"models_enriched.json"` found at line 12 of `generate_visuals.py`.

**Step 3: Apply fix**

In `generate_visuals.py`:

1. Add import at top with other stdlib imports:

```python
from atlas_schemas.config import settings
```

2. Change line 12 inside `main()`:

```python
# BEFORE
def main():
    data_path = "models_enriched.json"

# AFTER
def main():
    data_path = str(settings.PROJECT_ROOT / settings.OUTPUT_FILE)
```

**Step 4: Run tests**

```bash
pytest tests/test_generate_visuals.py -v
pytest --tb=short -q
```

Expected: all PASS.

**Step 5: Commit**

```bash
git add generate_visuals.py tests/test_generate_visuals.py
git commit -m "fix: use settings.PROJECT_ROOT / settings.OUTPUT_FILE in generate_visuals"
```

---

### Task 4: Fix enrich_metadata.py hardcoded dirs (Issue #172)

**Files:**
- Modify: `atlas_schemas/config.py` (add `PROMPTS_DIR`)
- Modify: `tools/enrich_metadata.py` (lines 11-13)
- Test: `tests/test_enrich_metadata.py` (extend — file already exists)

**Root cause:** Lines 11-13 of `tools/enrich_metadata.py` define `MODELS_DIR`, `PROMPTS_DIR`, and `ENRICHED_OUTPUTS_DIR` as bare strings. `settings.MODELS_DIR` and `settings.ENRICHED_OUTPUTS_DIR` already exist in `atlas_schemas/config.py` as absolute `Path` objects but are ignored. `PROMPTS_DIR` must be added to `Config` first.

**Existing test compatibility note:** `tests/test_enrich_metadata.py` uses `monkeypatch.setattr(em, "PROMPTS_DIR", str(tmp_path / ...))`. After this fix the module attribute becomes a `Path`, but `monkeypatch.setattr` overwrites it with a `str` — this is fine since downstream `os.path.join` and `os.makedirs` accept both.

**Step 1: Write failing test**

Add to `tests/test_enrich_metadata.py`:

```python
def test_enrich_metadata_uses_settings_dirs():
    """enrich_metadata module-level constants must use settings, not hardcoded strings."""
    import tools.enrich_metadata as mod
    from atlas_schemas.config import settings
    assert mod.MODELS_DIR == settings.MODELS_DIR, (
        f"MODELS_DIR must equal settings.MODELS_DIR ({settings.MODELS_DIR}), got {mod.MODELS_DIR!r}"
    )
    assert str(mod.ENRICHED_OUTPUTS_DIR) == str(settings.ENRICHED_OUTPUTS_DIR), (
        f"ENRICHED_OUTPUTS_DIR must equal settings.ENRICHED_OUTPUTS_DIR, got {mod.ENRICHED_OUTPUTS_DIR!r}"
    )
    assert str(mod.PROMPTS_DIR) == str(settings.PROMPTS_DIR), (
        f"PROMPTS_DIR must equal settings.PROMPTS_DIR, got {mod.PROMPTS_DIR!r}"
    )
```

**Step 2: Run to verify failure**

```bash
pytest tests/test_enrich_metadata.py::test_enrich_metadata_uses_settings_dirs -v
```

Expected: FAIL — `AttributeError: type object 'Config' has no attribute 'PROMPTS_DIR'`.

**Step 3: Apply fixes**

**3a. Add `PROMPTS_DIR` to `atlas_schemas/config.py`** (after `ENRICHED_OUTPUTS_DIR`):

```python
# BEFORE
ENRICHED_OUTPUTS_DIR: Path = PROJECT_ROOT / "enriched_outputs"
DEBUG_DIR: Path = PROJECT_ROOT / "ollama_debug_dumps"

# AFTER
ENRICHED_OUTPUTS_DIR: Path = PROJECT_ROOT / "enriched_outputs"
PROMPTS_DIR: Path = PROJECT_ROOT / "enrichment_prompts"
DEBUG_DIR: Path = PROJECT_ROOT / "ollama_debug_dumps"
```

**3b. Update `tools/enrich_metadata.py` lines 11-13:**

```python
# BEFORE
LOG_FILE = settings.LOG_FILE
MODELS_DIR = "models"
PROMPTS_DIR = "enrichment_prompts"
ENRICHED_OUTPUTS_DIR = "enriched_outputs"

# AFTER
LOG_FILE = settings.LOG_FILE
MODELS_DIR = settings.MODELS_DIR
PROMPTS_DIR = settings.PROMPTS_DIR
ENRICHED_OUTPUTS_DIR = settings.ENRICHED_OUTPUTS_DIR
```

`settings` is already imported at line 7 (`from atlas_schemas.config import settings`), no new import needed.

**Step 4: Run tests**

```bash
pytest tests/test_enrich_metadata.py -v
pytest --tb=short -q
```

Expected: all PASS including the four pre-existing tests.

**Step 5: Commit**

```bash
git add atlas_schemas/config.py tools/enrich_metadata.py tests/test_enrich_metadata.py
git commit -m "fix: use settings for MODELS_DIR, PROMPTS_DIR, ENRICHED_OUTPUTS_DIR in enrich_metadata"
```

---

## Final Verification

```bash
pytest --tb=short -q
```

Expected: all passing. Close GH issues: #168, #169, #170, #171, #172.
