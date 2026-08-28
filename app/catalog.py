"""Parser for Kaggle's MovieLens 100K dataset; raw data is not redistributed."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re

from app.models import Movie

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "ml-100k"
GENRES = ["unknown", "Action", "Adventure", "Animation", "Children's", "Comedy", "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror", "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western"]


def data_available() -> bool:
    return (DATA_DIR / "u.data").exists() and (DATA_DIR / "u.item").exists()


def load_movielens() -> tuple[list[Movie], dict[int, dict[int, float]]]:
    if not data_available():
        raise FileNotFoundError("MovieLens data is missing. Run scripts/download_movielens.ps1 first.")
    ratings: dict[int, dict[int, float]] = defaultdict(dict)
    with (DATA_DIR / "u.data").open() as file:
        for line in file:
            user_id, movie_id, rating, _ = line.split("\t")
            ratings[int(user_id)][int(movie_id)] = float(rating)

    movie_ratings: dict[int, list[float]] = defaultdict(list)
    for user_ratings in ratings.values():
        for movie_id, rating in user_ratings.items():
            movie_ratings[movie_id].append(rating)

    movies: list[Movie] = []
    with (DATA_DIR / "u.item").open(encoding="latin-1") as file:
        for line in file:
            fields = line.rstrip("\n").split("|")
            year = re.search(r"(19|20)\d{2}", fields[1])
            genres = [genre for genre, bit in zip(GENRES, fields[5:]) if bit == "1" and genre != "unknown"]
            values = movie_ratings[int(fields[0])]
            movies.append(Movie(
                id=int(fields[0]),
                title=fields[1],
                year=int(year.group()) if year else None,
                genres=genres,
                rating=round(sum(values) / len(values), 2) if values else None,
                votes=len(values),
            ))
    return movies, dict(ratings)
