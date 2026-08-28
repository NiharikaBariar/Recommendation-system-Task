"""Data-availability evaluator for MovieLens 100K."""
from app.catalog import load_movielens
from app.models import RecommendRequest
from app.recommender import MovieLensRecommender


def main() -> None:
    movies, ratings = load_movielens()
    model = MovieLensRecommender(movies, ratings)
    available = sum(bool(model.recommend(RecommendRequest(user_id=user, limit=10))[1]) for user in list(ratings)[:20])
    print(f"Recommendation availability@10: {available / 20:.2f}")


if __name__ == "__main__":
    main()
