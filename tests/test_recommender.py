from app.models import Movie, RecommendRequest
from app.recommender import MovieLensRecommender

MOVIES = [Movie(id=1, title="Action One", genres=["Action"], year=1990), Movie(id=2, title="Action Two", genres=["Action"], year=2000), Movie(id=3, title="Comedy", genres=["Comedy"], year=2010), Movie(id=4, title="Action Three", genres=["Action"], year=2020)]
RATINGS = {1: {1: 5, 3: 1}, 2: {1: 5, 2: 5, 4: 4}, 3: {1: 4, 2: 5, 4: 5}, 4: {1: 1, 3: 5}}


def test_seed_fallback_excludes_seed_and_explains():
    model = MovieLensRecommender(MOVIES, RATINGS)
    strategy, results = model.recommend(RecommendRequest(seed_movie_id=1, limit=2))
    assert strategy == "content_genre_fallback"
    assert all(item.movie.id != 1 and item.explanation for item in results)


def test_cold_start_prefers_requested_genre():
    model = MovieLensRecommender(MOVIES, RATINGS)
    _, results = model.recommend(RecommendRequest(genres=["Comedy"], limit=1))
    assert results[0].movie.id == 3


def test_known_user_uses_collaborative_filtering():
    model = MovieLensRecommender(MOVIES, RATINGS)
    strategy, results = model.recommend(RecommendRequest(user_id=1, limit=2))
    assert strategy == "popularity_cold_start_fallback"
    assert results
    assert all(item.movie.id not in RATINGS[1] for item in results)


def test_discovery_filters_apply_to_recommendations():
    model = MovieLensRecommender(MOVIES, RATINGS)
    _, results = model.recommend(RecommendRequest(genres=["Action"], year_from=2000, min_rating=4, min_votes=2, limit=5))
    assert [item.movie.id for item in results] == [2, 4]


def test_sparse_known_user_falls_back_to_seed():
    model = MovieLensRecommender(MOVIES, RATINGS)
    strategy, results = model.recommend(RecommendRequest(user_id=4, seed_movie_id=2, limit=1))
    assert strategy == "content_genre_fallback"
    assert results[0].movie.id == 4
