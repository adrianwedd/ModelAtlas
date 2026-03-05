import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from atlas_schemas.config import settings


def main():
    # Resolve paths relative to this file
    BASE_DIR = Path(__file__).resolve().parent

    # Guard: exit gracefully if data file is missing
    data_path = settings.PROJECT_ROOT / settings.OUTPUT_FILE
    if not data_path.exists():
        print(
            f"Error: Data file '{data_path}' not found. Run the enrichment trace first.",  # noqa: E501
            file=sys.stderr,
        )
        sys.exit(1)

    # Load template
    env = Environment(loader=FileSystemLoader(BASE_DIR / "templates"))
    template = env.get_template("README.md.j2")

    # Load data
    with open(data_path, "r", encoding="utf-8") as f:
        models = json.load(f)

    # Render and write
    readme = template.render(
        models=models, date=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    with open(BASE_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)


if __name__ == "__main__":
    main()
