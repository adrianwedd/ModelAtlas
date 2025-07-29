from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
from pathlib import Path

# Assuming models_similar.json is in the data directory
MODELS_SIMILAR_PATH = Path(__file__).parent.parent / "data" / "models_similar.json"

app = FastAPI()

class Model(BaseModel):
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
    tags: List[str] = []
    annotations: dict = {}
    quality_score: dict = {}
    trust_score: Optional[float] = None
    similar_models: List[dict] = [] # Assuming similar models are also dicts

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
