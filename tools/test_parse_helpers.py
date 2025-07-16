from scrape_ollama import parse_pull_count, get_hash

def test_parse_pull_count_variants():
    assert parse_pull_count("123") == 123
    assert parse_pull_count("1.2K Downloads") == 1200
    assert parse_pull_count("3.4M Downloads") == 3_400_000
    assert parse_pull_count(None) == 0
    assert parse_pull_count("invalid") == 0

def test_get_hash_consistency():
    h1 = get_hash("hello")
    h2 = get_hash("hello")
    assert isinstance(h1, str) and len(h1) == 12
    assert h1 == h2