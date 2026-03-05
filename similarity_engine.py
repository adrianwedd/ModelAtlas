"""ModelSimilarityEngine: name-based and metadata-based model similarity."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Architecture family normalization map.
# Each key is the canonical family name; values are substrings that, when
# found in a lowercased model name, map to that family.
# Order matters: more specific entries must come before more general ones
# so that e.g. "codellama" is tried before "llama".
_ARCH_MAP: list[tuple[str, list[str]]] = [
    ("llama", ["codellama", "llama", "vicuna", "alpaca", "wizardlm"]),
    ("mistral", ["mistral", "mixtral"]),
    ("phi", ["phi"]),
    ("qwen", ["qwen"]),
    ("gemma", ["gemma"]),
    ("falcon", ["falcon"]),
    ("mpt", ["mpt"]),
    ("bloom", ["bloom"]),
    ("gpt", ["gpt2", "gpt"]),
]

_PARAM_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[Bb]", re.IGNORECASE)
_VARIANT_KEYWORDS = {
    "instruct",
    "chat",
    "code",
    "base",
    "gguf",
    "q4",
    "q8",
    "fp16",
    "awq",
}


@dataclass
class SimilarityResult:
    model_a: str
    model_b: str
    score: float
    reasons: list[str] = field(default_factory=list)


class ModelSimilarityEngine:
    """Computes similarity between AI models by name and metadata."""

    def __init__(self) -> None:
        self.models_data: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Name-based similarity helpers
    # ------------------------------------------------------------------

    def normalize_architecture(self, name: str) -> str:
        """Return canonical architecture family for a model name."""
        if name is None:
            return ""
        lower = name.lower()
        for family, patterns in _ARCH_MAP:
            if any(p in lower for p in patterns):
                return family
        # Fallback: first token before any separator
        base = re.split(r"[-:_.]", lower)[0]
        return base

    def extract_parameter_count(self, name: str) -> float | None:
        """Extract parameter count in billions, e.g. '7b' -> 7.0, '2.7b' -> 2.7."""
        if name is None:
            return None
        m = _PARAM_RE.search(name)
        return float(m.group(1)) if m else None

    def _extract_variants(self, name: str) -> set[str]:
        if name is None:
            return set()
        parts = re.split(r"[-:_.]", name.lower())
        return {p for p in parts if p in _VARIANT_KEYWORDS}

    def _extract_base_token(self, name: str) -> str:
        """Return the first meaningful token of the model name (before any separator)."""  # noqa: E501
        if name is None:
            return ""
        # Strip Hugging Face org prefix if present (e.g. "meta-llama/Llama-3" -> "Llama-3")  # noqa: E501
        if "/" in name:
            name = name.split("/", 1)[1]
        lower = name.lower()
        # First token before separator
        return re.split(r"[-:_.]", lower)[0]

    def calculate_name_similarity(
        self, name_a: str, name_b: str
    ) -> tuple[float, list[str]]:
        """
        Compare two model name strings.
        Returns (score 0.0-1.0, list of human-readable reasons).

        Score rules:
        - Same specific base token + same params -> 1.0 (full base model match)
        - Same architecture family: +0.4
        - Same parameter count: +0.3
        - Similar parameter count (within 1B): +0.2
        - Common variant keywords: +0.2
        """
        reasons: list[str] = []

        arch_a = self.normalize_architecture(name_a)
        arch_b = self.normalize_architecture(name_b)
        base_a = self._extract_base_token(name_a)
        base_b = self._extract_base_token(name_b)
        params_a = self.extract_parameter_count(name_a)
        params_b = self.extract_parameter_count(name_b)
        variants_a = self._extract_variants(name_a)
        variants_b = self._extract_variants(name_b)
        common_variants = variants_a & variants_b

        # Full base model match: same specific base token + same params.
        # Use the base token (e.g. "llama3") not the normalized family ("llama")
        # so that "codellama" vs "llama2" do NOT trigger this path.
        if (
            base_a
            and base_b
            and base_a == base_b
            and params_a is not None
            and params_a == params_b
        ):
            reasons.append(f"Same base model ({base_a})")
            reasons.append(f"Same parameter count ({params_a}B)")
            if common_variants:
                reasons.append(f"Common variants: {', '.join(sorted(common_variants))}")
            return 1.0, reasons

        score = 0.0

        if arch_a and arch_b and arch_a == arch_b:
            score += 0.4
            reasons.append(f"Same architecture family ({arch_a})")

        if params_a is not None and params_b is not None:
            if params_a == params_b:
                score += 0.3
                reasons.append(f"Same parameter count ({params_a}B)")
            elif abs(params_a - params_b) <= 1.0:
                score += 0.2
                reasons.append(f"Similar parameter count ({params_a}B vs {params_b}B)")

        if common_variants:
            score += 0.2
            reasons.append(f"Common variants: {', '.join(sorted(common_variants))}")

        return round(min(score, 1.0), 2), reasons

    # ------------------------------------------------------------------
    # Metadata-based similarity
    # ------------------------------------------------------------------

    def _metadata_similarity(self, a: dict, b: dict) -> float:
        score = 0.0
        for field_name, weight in [
            ("architecture_family", 0.25),
            ("training_approach", 0.15),
            ("license_category", 0.10),
            ("recommended_hardware", 0.10),
        ]:
            if a.get(field_name) and a.get(field_name) == b.get(field_name):
                score += weight

        uc_a = {
            u.get("use_case")
            for u in a.get("optimal_use_cases", [])
            if u.get("use_case")
        }
        uc_b = {
            u.get("use_case")
            for u in b.get("optimal_use_cases", [])
            if u.get("use_case")
        }
        if uc_a and uc_b:
            score += 0.20 * len(uc_a & uc_b) / len(uc_a | uc_b)

        tok_a = set(a.get("summary", "").lower().split())
        tok_b = set(b.get("summary", "").lower().split())
        if tok_a and tok_b:
            score += 0.20 * len(tok_a & tok_b) / len(tok_a | tok_b)

        return round(min(score, 1.0), 3)

    def find_similar_models(self, name: str, top_k: int = 5) -> list[SimilarityResult]:
        """Return top-k most similar models from models_data for the given name."""
        data_a = self.models_data.get(name, {})
        results: list[SimilarityResult] = []
        for other_name, data_b in self.models_data.items():
            if other_name == name:
                continue
            name_score, reasons = self.calculate_name_similarity(name, other_name)
            meta_score = self._metadata_similarity(data_a, data_b)
            combined = round(0.5 * name_score + 0.5 * meta_score, 3)
            results.append(SimilarityResult(name, other_name, combined, reasons))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def detect_duplicates(self, threshold: float = 0.9) -> list[tuple[str, str, float]]:
        """Return pairs whose combined similarity exceeds threshold."""
        names = list(self.models_data.keys())
        duplicates: list[tuple[str, str, float]] = []
        for i, a in enumerate(names):
            for b in names[i + 1 :]:
                name_score, _ = self.calculate_name_similarity(a, b)
                meta_score = self._metadata_similarity(
                    self.models_data[a], self.models_data[b]
                )
                combined = round(0.5 * name_score + 0.5 * meta_score, 3)
                if combined >= threshold:
                    duplicates.append((a, b, combined))
        return duplicates

    def generate_similarity_graph(self, threshold: float = 0.3) -> dict:
        """Return graph dict with nodes and edges for all pairs above threshold."""
        names = list(self.models_data.keys())
        nodes = [{"id": n} for n in names]
        edges = []
        for i, a in enumerate(names):
            for b in names[i + 1 :]:
                name_score, reasons = self.calculate_name_similarity(a, b)
                meta_score = self._metadata_similarity(
                    self.models_data[a], self.models_data[b]
                )
                combined = round(0.5 * name_score + 0.5 * meta_score, 3)
                if combined >= threshold:
                    edges.append(
                        {
                            "source": a,
                            "target": b,
                            "weight": combined,
                            "reasons": reasons,
                        }
                    )
        return {"nodes": nodes, "edges": edges}
