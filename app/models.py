from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class Movie(BaseModel):
    id: int
    title: str
    genres: list[str]
    year: int | None = None
    rating: float | None = None
    votes: int | None = None


class RecommendRequest(BaseModel):
    user_id: int | None = Field(default=None, ge=1)
    seed_movie_id: int | None = Field(default=None, ge=1)
    genres: list[str] = Field(default_factory=list)
    year_from: int | None = Field(default=None, ge=1900, le=2100)
    year_to: int | None = Field(default=None, ge=1900, le=2100)
    min_rating: float | None = Field(default=None, ge=0, le=5)
    min_votes: int | None = Field(default=None, ge=0)
    exclude_ids: list[int] = Field(default_factory=list)
    limit: int = Field(default=8, ge=1, le=20)

    @model_validator(mode="after")
    def validate_year_range(self) -> "RecommendRequest":
        if self.year_from is not None and self.year_to is not None and self.year_from > self.year_to:
            raise ValueError("year_from must be less than or equal to year_to")
        return self


class Recommendation(BaseModel):
    movie: Movie
    score: float
    explanation: str
    signals: dict[str, float]


class RecommendResponse(BaseModel):
    strategy: str
    recommendations: list[Recommendation]
