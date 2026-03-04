import json
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def main():
    # Resolve paths relative to this file
    BASE_DIR = Path(__file__).resolve().parent

    # Load template
    env = Environment(loader=FileSystemLoader(BASE_DIR / "templates"))
    template = env.get_template("README.md.j2")

    # Load data
    with open(BASE_DIR / "models_enriched.json", "r", encoding="utf-8") as f:
        models = json.load(f)

    # Render and write
    readme = template.render(models=models, date=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    with open(BASE_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)


if __name__ == "__main__":
    main()
