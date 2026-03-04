"""Tests for tools/normalize_and_validate.py"""


def test_validate_and_normalize_uses_logger_not_print():
    """validate_and_normalize_models must use logger, not print()."""
    import inspect

    from tools.normalize_and_validate import validate_and_normalize_models

    src = inspect.getsource(validate_and_normalize_models)
    assert "print(" not in src, "Must use logger, not print()"
