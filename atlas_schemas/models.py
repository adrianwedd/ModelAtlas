from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class TraceableItem(BaseModel):
    """Represents a single item that flows through the pipeline with provenance."""
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

class PipelineConfig(BaseModel):
    """Represents the configuration for a pipeline run."""
    name: str
    stages: List[Dict[str, Any]] = Field(default_factory=list)
    # Add other pipeline-specific configurations
    output_dir: Optional[str] = None

# You can add more models here as needed, e.g., for specific enrichment outputs