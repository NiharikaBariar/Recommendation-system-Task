from __future__ import annotations

from collections import Counter
from math import sqrt

from app.models import Movie, Recommendation, RecommendRequest


class MovieLensRecommender:
    """Mean-centred user-user collaborative filter with cold-start fallbacks."""

    def __init__(self, movies: list[Movie], ratings: dict[int, dict[int, float]]) -> None:
        self.movies, self.ratings = movies, ratings
        self.by_id = {movie.id: movie for movie in movies}
        self.means = {user: sum(values.values()) / len(values) for user, values in ratings.items()}
        self.counts = Counter(mid for values in ratings.values() for mid in values)
        self.movie_mean = {mid: sum(values[mid] for values in ratings.values() if mid in values) / count for mid, count in self.counts.items()}

    def _similarity(self, target: int, other: int) -> float:
        common = set(self.ratings[target]) & set(self.ratings[other])
        if len(common) < 3:
            return 0.0
        dot = sum((self.ratings[target][m] - self.means[target]) * (self.ratings[other][m] - self.means[other]) for m in common)
        left = sqrt(sum((self.ratings[target][m] - self.means[target]) ** 2 for m in common))
        right = sqrt(sum((self.ratings[other][m] - self.means[other]) ** 2 for m in common))
        return (dot / (left * right) if left and right else 0.0) * len(common) / (len(common) + 10)

    def recommend(self, request: RecommendRequest) -> tuple[str, list[Recommendation]]:
        excluded = set(request.exclude_ids)
        eligible = self._eligible(request)
        if request.user_id in self.ratings:
            collaborative = self._for_user(request.user_id, excluded, request.limit, eligible)
            if collaborative:
                return "user_user_collaborative_filtering", collaborative
        if request.seed_movie_id in self.by_id:
            seed_results = self._for_seed(request.seed_movie_id, excluded, request.limit, eligible)
            if seed_results:
                return "content_genre_fallback", seed_results
        return "popularity_cold_start_fallback", self._popular(request.genres, excluded, request.limit, eligible)

    def _eligible(self, request: RecommendRequest) -> set[int]:
        wanted = {genre.lower() for genre in request.genres}
        return {
            movie.id for movie in self.movies
            if (not wanted or wanted & {genre.lower() for genre in movie.genres})
            and (request.year_from is None or movie.year is not None and movie.year >= request.year_from)
            and (request.year_to is None or movie.year is not None and movie.year <= request.year_to)
            and (request.min_rating is None or self.movie_mean.get(movie.id, 0) >= request.min_rating)
            and (request.min_votes is None or self.counts[movie.id] >= request.min_votes)
        }

    def _for_user(self, user: int, excluded: set[int], limit: int, eligible: set[int]) -> list[Recommendation]:
        watched = set(self.ratings[user]) | excluded
        neighbours = sorted(((other, self._similarity(user, other)) for other in self.ratings if other != user), key=lambda item: item[1], reverse=True)[:80]
        scored = []
        for mid in self.by_id:
            if mid in watched or mid not in eligible:
                continue
            weights = [(sim, self.ratings[other][mid] - self.means[other]) for other, sim in neighbours if sim > 0 and mid in self.ratings[other]]
            if len(weights) < 2:
                continue
            score = self.means[user] + sum(sim * delta for sim, delta in weights) / sum(abs(sim) for sim, _ in weights)
            scored.append((mid, min(5.0, max(1.0, score)), len(weights)))
        ranked = sorted(scored, key=lambda item: item[1], reverse=True)[:limit]
        return [self._present(self.by_id[mid], score, "Similar users rated this highly.", {"predicted_rating": round(score, 2), "neighbours": float(n)}) for mid, score, n in ranked]

    def _for_seed(self, seed_id: int, excluded: set[int], limit: int, eligible: set[int]) -> list[Recommendation]:
        seed = self.by_id[seed_id]
        ranked = sorted((m for m in self.movies if m.id in eligible and m.id not in excluded | {seed_id}), key=lambda m: (len(set(seed.genres) & set(m.genres)), self.movie_mean.get(m.id, 0)), reverse=True)[:limit]
        return [self._present(m, self.movie_mean.get(m.id, 0), f"Shares genres with {seed.title}.", {"mean_rating": round(self.movie_mean.get(m.id, 0), 2), "shared_genres": float(len(set(seed.genres) & set(m.genres)) )}) for m in ranked]

    def _popular(self, genres: list[str], excluded: set[int], limit: int, eligible: set[int]) -> list[Recommendation]:
        ranked = sorted((m for m in self.movies if m.id in eligible and m.id not in excluded), key=lambda m: (self.counts[m.id] >= 50, self.movie_mean.get(m.id, 0), self.counts[m.id]), reverse=True)[:limit]
        return [self._present(m, self.movie_mean.get(m.id, 0), "A popular, well-rated catalogue choice.", {"mean_rating": round(self.movie_mean.get(m.id, 0), 2), "rating_count": float(self.counts[m.id])}) for m in ranked]

    @staticmethod
    def _present(movie: Movie, score: float, explanation: str, signals: dict[str, float]) -> Recommendation:
        return Recommendation(movie=movie, score=round(score, 3), explanation=explanation, signals=signals)
