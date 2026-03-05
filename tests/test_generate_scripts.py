import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def test_generate_visuals_exits_gracefully_without_data(tmp_path, monkeypatch):
    """generate_visuals.main() must not raise FileNotFoundError when data is missing."""
    monkeypatch.chdir(tmp_path)
    import importlib

    import generate_visuals

    importlib.reload(generate_visuals)
    try:
        generate_visuals.main()
    except FileNotFoundError:
        pytest.fail(
            "generate_visuals.main() raised FileNotFoundError on missing data file"
        )
    except SystemExit:
        pass  # Graceful exit with error code is acceptable


def test_generate_readme_exits_gracefully_without_data(tmp_path, monkeypatch):
    """generate_readme.main() must not raise FileNotFoundError when data is missing."""
    monkeypatch.chdir(tmp_path)
    import importlib

    import generate_readme

    importlib.reload(generate_readme)
    try:
        generate_readme.main()
    except FileNotFoundError:
        pytest.fail(
            "generate_readme.main() raised FileNotFoundError on missing data file"
        )
    except SystemExit:
        pass  # Graceful exit with error code is acceptable
    except Exception:
        pass  # Other errors (missing template etc) acceptable, FileNotFoundError is not
