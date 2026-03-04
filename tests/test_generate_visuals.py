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
