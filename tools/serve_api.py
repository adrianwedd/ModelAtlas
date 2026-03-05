import json
import logging
import sys
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException

# Add the project root to sys.path to enable imports from atlas_schemas
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from atlas_schemas.config import settings  # noqa: E402
from atlas_schemas.models import Model  # noqa: E402

logger = logging.getLogger(__name__)

MODELS_DATA_PATH = settings.PROJECT_ROOT / settings.OUTPUT_FILE

app = FastAPI(title="ModelAtlas API")


# Load models data
def load_models_data():
    if not MODELS_DATA_PATH.exists():
        return []
    try:
        with open(MODELS_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error("Catalog JSON is corrupted: %s", e)
        return []


@app.get("/models", response_model=List[Model])
async def get_all_models():
    return load_models_data()


@app.get("/models/{model_name}", response_model=Model)
async def get_model_by_name(model_name: str):
    for model in load_models_data():
        if model["name"] == model_name:
            return model
    raise HTTPException(status_code=404, detail="Model not found")


@app.get("/models/{model_name}/similar", response_model=List[dict])
async def get_similar_models(model_name: str):
    for model in load_models_data():
        if model["name"] == model_name:
            return model.get("similar_models", [])
    raise HTTPException(status_code=404, detail="Model not found")


# To run this API, save it as serve_api.py and run:
# uvicorn serve_api:app --reload
