import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from similarity_engine import ModelSimilarityEngine

# Avoid config initialization issues in imported modules
os.environ.setdefault("LLM_API_KEY", "dummy")

engine = ModelSimilarityEngine()


def test_exact_base_match_with_params():
    score, reasons = engine.calculate_name_similarity("llama3:8b", "llama3:8b-instruct")
    assert score == 1.0
    assert "Same base model (llama3)" in reasons
    assert "Same parameter count (8.0B)" in reasons


def test_architecture_and_variant_similarity():
    score, reasons = engine.calculate_name_similarity("codellama:7b-instruct", "llama2:7b-instruct")
    assert score == pytest.approx(0.9)
    assert "Same architecture family (llama)" in reasons
    assert "Same parameter count (7.0B)" in reasons
    assert "Common variants: instruct" in reasons


def test_parameter_difference_within_one():
    score, reasons = engine.calculate_name_similarity("phi-2.7b", "phi-3b")
    assert score == pytest.approx(0.6)
    assert "Similar parameter count (2.7B vs 3.0B)" in reasons


def test_no_similarity():
    score, reasons = engine.calculate_name_similarity("llama3", "mistral")
    assert score == 0.0
    assert reasons == []


def test_helper_functions_and_graph_generation():
    # Exercise helper utilities for coverage
    assert engine.normalize_architecture("Vicuna-13B") == "llama"
    assert engine.normalize_architecture("Custom") == "custom"
    assert engine.extract_parameter_count("model-5b") == 5.0

    model_a = {
        "id": "a",
        "architecture_family": "llama",
        "training_approach": "sft",
        "optimal_use_cases": [{"use_case": "chat"}],
        "license_category": "permissive",
        "recommended_hardware": "gpu",
        "summary": "hello world",
        "primary_strengths": ["fast"],
        "known_limitations": ["none"],
        "tags": ["chat"],
    }
    model_b = {
        "id": "b",
        "architecture_family": "llama",
        "training_approach": "sft",
        "optimal_use_cases": [{"use_case": "chat"}, {"use_case": "code"}],
        "license_category": "permissive",
        "recommended_hardware": "gpu",
        "summary": "hello world",
        "primary_strengths": ["fast"],
        "known_limitations": ["none"],
        "tags": ["chat"],
    }

    engine.models_data = {"llama3:8b": model_a, "llama2:7b-instruct": model_b}

    sims = engine.find_similar_models("llama3:8b")
    assert sims and sims[0].model_b == "llama2:7b-instruct"

    dups = engine.detect_duplicates(threshold=0.5)
    assert ("llama3:8b", "llama2:7b-instruct",) in [(a, b) for a, b, _ in dups]

    graph = engine.generate_similarity_graph()
    assert {"nodes", "edges"} <= graph.keys()
