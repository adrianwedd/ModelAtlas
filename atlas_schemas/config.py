from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

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
    LLM_MODEL_NAME: str = "gemini-1.5-pro"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Create a singleton instance of the Config
settings = Config()
