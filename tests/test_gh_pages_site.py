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
    assert (
        "upload-pages-artifact" in content
    ), "pages.yml must use upload-pages-artifact"
    assert (
        "models_enriched.json" in content
    ), "pages.yml must copy models_enriched.json into site/"


def test_html_has_required_elements():
    """index.html must have required section IDs and data attributes."""
    from bs4 import BeautifulSoup

    html = (SITE / "index.html").read_text()
    soup = BeautifulSoup(html, "html.parser")

    assert soup.find(id="licenseChart"), "missing #licenseChart canvas"
    assert soup.find(id="trustChart"), "missing #trustChart canvas"
    assert soup.find(id="tagsChart"), "missing #tagsChart canvas"
    assert soup.find(class_="model-table"), "missing .model-table"
    assert soup.find(class_="search-input"), "missing .search-input"
    assert soup.find(class_="asr-col"), "missing .asr-col (ASR column header)"
    assert soup.find(
        class_="stat-chip--pending"
    ), "missing .stat-chip--pending (ASR stat)"
    assert "x-data" in html, "missing Alpine.js x-data attribute"
    assert "alpinejs" in html, "missing Alpine.js CDN link"
    assert "chart.js" in html, "missing Chart.js CDN link"


def test_app_js_has_required_functions():
    """app.js must define modelApp() and required methods."""
    src = (SITE / "app.js").read_text()
    required = [
        "function modelApp",
        "async init",
        "applyFilters",
        "trustDots",
        "topTags",
        "modelUrl",
        "licenseBadgeClass",
        "initLicenseChart",
        "initTrustChart",
        "initTagsChart",
        "TAG_BLOCKLIST",
    ]
    for name in required:
        assert name in src, f"app.js missing: {name}"
