"""Tests for enrich/main.py"""


def test_run_enrichment_trace_uses_settings_validated_models_dir():
    """run_enrichment_trace must not hardcode 'data/validated' path."""
    import inspect

    from enrich.main import run_enrichment_trace

    src = inspect.getsource(run_enrichment_trace)
    assert (
        '"data/validated"' not in src
    ), "run_enrichment_trace must not hardcode 'data/validated' — use settings or parameter"
