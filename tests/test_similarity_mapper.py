"""Tests for tools/similarity_mapper.py"""


def test_similarity_mapper_uses_logger_not_print():
    """similarity_mapper.main must use logger, not print()."""
    import inspect

    import tools.similarity_mapper as mod

    src = inspect.getsource(mod.main)
    assert "print(" not in src, "Must use logger, not print()"
