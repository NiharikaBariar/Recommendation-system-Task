from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from app.catalog import data_available, load_movielens
from app.models import RecommendRequest, RecommendResponse
from app.recommender import MovieLensRecommender

app = FastAPI(title="Screenova MovieLens", version="2.0.0")
_recommender: MovieLensRecommender | None = None


def get_recommender() -> MovieLensRecommender:
    global _recommender
    if not data_available():
        raise HTTPException(503, "Dataset unavailable. Configure Kaggle credentials and run scripts/download_movielens.ps1.")
    if _recommender is None:
        movies, ratings = load_movielens()
        _recommender = MovieLensRecommender(movies, ratings)
    return _recommender


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok" if data_available() else "dataset_not_loaded"}


@app.get("/api/movies")
def movies():
    return get_recommender().movies


@app.post("/api/recommendations", response_model=RecommendResponse)
def recommendations(request: RecommendRequest) -> RecommendResponse:
    strategy, result = get_recommender().recommend(request)
    return RecommendResponse(strategy=strategy, recommendations=result)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    template = Path(__file__).parent / "templates" / "index.html"
    return template.read_text(encoding="utf-8")
