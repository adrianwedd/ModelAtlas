import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
WORKFLOWS = ROOT / ".github" / "workflows"


def test_site_files_exist():
    """site/ scaffold must have index.html, style.css, app.js."""
    assert (SITE / "index.html").exists(), "site/index.html missing"
    assert (SITE / "style.css").exists(), "site/style.css missing"
    assert (SITE / "app.js").exists(), "site/app.js missing"


def test_pages_workflow_exists():
    """pages.yml must exist and reference deploy-pages action."""
    wf = WORKFLOWS / "pages.yml"
    assert wf.exists(), ".github/workflows/pages.yml missing"
    content = wf.read_text()
    assert "deploy-pages" in content, "pages.yml must use actions/deploy-pages"
    assert "upload-pages-artifact" in content, "pages.yml must use upload-pages-artifact"
    assert "models_enriched.json" in content, "pages.yml must copy models_enriched.json into site/"
