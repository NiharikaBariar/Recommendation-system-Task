# CineMatch engineering guide - MovieLens revision

## What changed

CineMatch now uses Kaggle's [MovieLens 100K dataset](https://www.kaggle.com/datasets/bhatvikas/movielens-100k-dataset), not a synthetic catalogue. The dataset provides 100,000 1-5 ratings from 943 users over 1,682 films, enabling collaborative filtering based on genuine user-item interactions.

## Dataset acquisition and governance

Raw source data is not committed or redistributed. Configure a personal Kaggle API token, then run `scripts/download_movielens.ps1`. It obtains the archive using the Kaggle CLI and expands it under `data/raw/ml-100k/`; that directory and credentials are excluded from Git. This respects the dataset's stated redistribution and commercial-use constraints. Retain GroupLens attribution in any public submission.

## Architecture

```text
Kaggle API -> data/raw/ml-100k/{u.data,u.item} -> parser -> in-memory ranker
Browser UI -> FastAPI -> user-user CF | genre fallback | popularity fallback
```

`u.data` provides users, movies, ratings, and timestamps. `u.item` provides title and multi-hot genre metadata. The parser lives behind `app/catalog.py`, so replacing raw files with a warehouse/feature-store client leaves the application API unchanged.

## Ranking methodology

For a known user, CineMatch calculates mean-centred Pearson similarity against every other user on co-rated titles. A shrinkage factor, `overlap / (overlap + 10)`, lowers confidence in small overlaps. The strongest 80 neighbours produce weighted predicted ratings for unseen movies; candidates require two positive neighbour ratings.

Cold-start behaviour is explicit. A seed movie yields a genre-overlap ranking, and no-history/no-seed requests use a popularity fallback with a 50-rating reliability threshold. Each recommendation returns an explanation and the rank signals used, so the UI does not present a black-box score.

## Evaluation and tests

The included evaluator is a data-availability smoke test. A production evaluation must use a timestamp-based train/holdout split and report Precision@K, Recall@K, NDCG@K, coverage, diversity, novelty, p50/p95 latency, and segmented quality versus popularity and content-only baselines. Run `pytest -q` for deterministic unit tests covering personalized CF selection, seed exclusion/explanation, and cold-start genre prioritization.

## Limitations and roadmap

MovieLens 100K is old, sparse, and ratings-only; it lacks current catalogue attributes, browsing context, implicit feedback, safety labels, and modern user behaviour. User-user CF also does not scale as catalogue and user count grow. The production roadmap is governed event capture, offline features, two-tower candidate retrieval, learning-to-rank re-ranking, ANN serving, caching, monitoring/drift controls, consent/deletion workflows, and A/B testing using watch-start, completion, save, and long-term satisfaction metrics.
