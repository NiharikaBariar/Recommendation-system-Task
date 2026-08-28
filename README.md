# Screenova - MovieLens Collaborative Recommendations

An explainable recommendation system built around Kaggle's public [MovieLens 100K dataset](https://www.kaggle.com/datasets/bhatvikas/movielens-100k-dataset): 100,000 ratings from 943 users across 1,682 films. It replaces the earlier synthetic catalogue with a genuine user-item interaction dataset.

## Setup

1. Create a Kaggle API token from your Kaggle account settings and configure it as documented by Kaggle. Never commit `kaggle.json`.
2. Install the dependencies and pull the dataset. If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\scripts\download_movielens.ps1
```

The script expects a valid Kaggle API token at `$HOME/.kaggle/kaggle.json` and writes the extracted data to `data/raw/` under the repository root.

3. Run the application:

```powershell
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000`; use a MovieLens user ID (1-943) to exercise personalized collaborative filtering. The UI also supports familiar discovery parameters: genres, release-year range, minimum rating (MovieLens' 1-5 scale), minimum votes, seed movie, and result count. `/docs` exposes the API contract.

## Validation

```powershell
pytest -q
```

Raw data remains in `data/raw/` and is ignored by Git because the source dataset's licence restricts redistribution. The acquisition script is the reproducible data dependency.

## Deployment

### Docker (recommended)

1. Download the dataset in a controlled build or release step; do not copy `kaggle.json` into the image.
2. Build and run:

```powershell
docker build -t screenova .
docker run --rm -p 8000:8000 -v ${PWD}\data\raw:/app/data/raw screenova
```

3. Put a TLS reverse proxy (such as Caddy, Nginx, or a cloud load balancer) in front of port 8000. Set health checks to `GET /health`.

### Managed hosting

Deploy the repository to a container-capable service such as Azure Container Apps, Google Cloud Run, AWS App Runner, or Render. Build with the included `Dockerfile`, provide `data/raw/ml-100k` through a persistent volume or release artifact, and set the platform `PORT` environment variable. Keep dataset acquisition outside the image and store credentials only in the platform secret manager.

For production, add a persistent feature/data store, cache the in-memory model warm-up, restrict CORS, add structured logs and metrics, and pin a supported Python base image. See [the engineering guide](docs/ENGINEERING_GUIDE.md) for the system design and roadmap.
