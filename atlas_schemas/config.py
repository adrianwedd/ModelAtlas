from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional


class Config(BaseSettings):
    """Centralized configuration for the ModelAtlas project."""

    PROJECT_NAME: str = "ModelAtlas"
    PROJECT_ROOT: Path = Path(__file__).parent.parent

    MODELS_DIR: Path = PROJECT_ROOT / "models"
    ENRICHED_OUTPUTS_DIR: Path = PROJECT_ROOT / "enriched_outputs"
    DEBUG_DIR: Path = PROJECT_ROOT / "ollama_debug_dumps"
    LOG_FILE: Path = PROJECT_ROOT / "ollama_scraper.log"
    OUTPUT_FILE: str = "models_enriched.json"

    OLLAMA_BASE_URL: str = "https://ollama.com"
    OLLAMA_REGISTRY_URL: str = "https://registry.ollama.ai"

    LLM_API_KEY: Optional[str] = None
    HUGGING_FACE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    PLAYWRIGHT_BROWSERS_PATH: Optional[str] = None
    LLM_MODEL_NAME: str = "gemini-1.5-pro"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Config()
