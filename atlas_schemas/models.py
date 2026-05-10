from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class TraceableItem(BaseModel):
    """Represents a single item that flows through the trace with provenance."""

    id: str
    content: str
    # Add other common fields that all traceable items should have
    # For example, a timestamp, source, etc.
    timestamp: Optional[str] = None
    source: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Model(BaseModel):
    """Represents a model with its metadata and scores."""

    name: str
    source: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    license: Optional[str] = None
    pull_count: Optional[int] = None
    last_updated: Optional[str] = None
    readme_html: Optional[str] = None
    readme_text: Optional[str] = None
    architecture: Optional[str] = None
    family: Optional[str] = None
    page_hash: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    annotations: Dict[str, Any] = Field(default_factory=dict)
    quality_score: Dict[str, Any] = Field(default_factory=dict)
    trust_score: Optional[float] = None
    similar_models: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("tags", mode="before")
    @classmethod
    def coerce_tags_to_strings(cls, v: Any) -> List[str]:
        if not isinstance(v, list):
            return []
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict) and "tag" in item:
                result.append(str(item["tag"]))
        return result

    @field_validator("architecture", mode="before")
    @classmethod
    def coerce_architecture_to_string(cls, v: Any) -> Optional[str]:
        if v is None or isinstance(v, str):
            return v
        if isinstance(v, dict):
            return v.get("modality") or next(
                (str(val) for val in v.values() if val), None
            )
        return str(v)


class TraceConfig(BaseModel):
    """Represents the configuration for a trace."""

    name: str
    stages: List[Dict[str, Any]] = Field(default_factory=list)
    # Add other trace-specific configurations
    output_dir: Optional[str] = None


# You can add more models here as needed, e.g., for specific enrichment outputs
