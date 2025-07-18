from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from pathlib import Path
from typing import Optional, List

class Config(BaseSettings):
    """Centralized configuration for the ModelAtlas project."""

    # General settings
    PROJECT_NAME: str = "ModelAtlas"
    PROJECT_ROOT: Path = Path(__file__).parent.parent

    # Data directories
    MODELS_DIR: Path = PROJECT_ROOT / "models"
    ENRICHED_OUTPUTS_DIR: Path = PROJECT_ROOT / "enriched_outputs"
    DEBUG_DIR: Path = PROJECT_ROOT / "ollama_debug_dumps"
    LOG_FILE: Path = PROJECT_ROOT / "ollama_scraper.log"

    # Ollama scraping settings
    OLLAMA_BASE_URL: str = "https://ollama.com"
    OLLAMA_REGISTRY_URL: str = "https://registry.ollama.ai"

    # LLM Enrichment settings
    LLM_API_KEY: Optional[str] = None
    HUGGING_FACE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    PLAYWRIGHT_BROWSERS_PATH: Optional[str] = None
    LLM_MODEL_NAME: str = "gemini-1.5-pro"

    REQUIRED_KEYS: List[str] = ["LLM_API_KEY"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_required_keys(cls, values: "Config") -> "Config":
        missing = [k for k in values.REQUIRED_KEYS if not getattr(values, k)]
        if missing:
            missing_str = ", ".join(missing)
            raise ValueError(
                f"Missing required configuration keys: {missing_str}. "
                "Set them in your environment or .env file."
            )
        return values

# Create a singleton instance of the Config
settings = Config()
