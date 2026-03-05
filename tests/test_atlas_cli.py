import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def test_default_tasks_yml_path_points_to_tasks_subdir():
    """The hardcoded default tasks.yml path must be under tasks/ subdir."""
    src = (PROJECT_ROOT / "atlas_cli" / "main.py").read_text()
    # Quick string check — the literal must not appear without "tasks/" prefix
    assert (
        '"tasks.yml"' not in src
        or 'tasks" / "tasks.yml"' in src
        or "tasks/tasks.yml" in src
    )


def test_run_routes_search_without_prepending_trace(monkeypatch):
    """_run() with 'search' as first arg must NOT prepend 'trace'."""
    called_args = []

    def fake_app(args=None):
        called_args.append(args)

    # Patch app in the module namespace
    import atlas_cli.main as cli_module

    monkeypatch.setattr(cli_module, "app", fake_app)
    monkeypatch.setattr("sys.argv", ["atlas", "search", "bert"])
    cli_module._run()

    assert called_args, "app was never called"
    # If routing is correct, app() called with no args (Typer reads sys.argv itself)
    # i.e. called_args[0] is None
    # If routing is WRONG, called_args[0] == ["trace", "search", "bert"]
    result = called_args[0]
    assert result is None or (
        isinstance(result, list) and result[0] != "trace"
    ), f"search was misrouted to trace: called with args={result}"
