import json
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException

# Add the project root to sys.path to enable imports from atlas_schemas
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from atlas_schemas.config import settings
from atlas_schemas.models import Model

# Assuming models_similar.json is in the data directory
MODELS_SIMILAR_PATH = settings.PROJECT_ROOT / "data" / "models_similar.json"

app = FastAPI(title="ModelAtlas API")


# Load models data
def load_models_data():
    if not MODELS_SIMILAR_PATH.exists():
        return []
    with open(MODELS_SIMILAR_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


models_data = load_models_data()


@app.get("/models", response_model=List[Model])
async def get_all_models():
    return models_data


@app.get("/models/{model_name}", response_model=Model)
async def get_model_by_name(model_name: str):
    for model in models_data:
        if model["name"] == model_name:
            return model
    raise HTTPException(status_code=404, detail="Model not found")


@app.get("/models/{model_name}/similar", response_model=List[dict])
async def get_similar_models(model_name: str):
    for model in models_data:
        if model["name"] == model_name:
            return model.get("similar_models", [])
    raise HTTPException(status_code=404, detail="Model not found")


# To run this API, save it as serve_api.py and run:
# uvicorn serve_api:app --reload
