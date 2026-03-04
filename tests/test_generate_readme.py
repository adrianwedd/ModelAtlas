"""Tests for generate_readme.py"""


def test_generate_readme_uses_settings_output_file():
    """generate_readme must not hardcode 'models_enriched.json'."""
    import inspect

    import generate_readme

    src = inspect.getsource(generate_readme.main)
    assert '"models_enriched.json"' not in src, (
        "generate_readme must use settings.OUTPUT_FILE, not hardcode the filename"
    )
