#!/bin/sh
set -eu

if [ ! -f /app/data/raw/ml-100k/u.data ]; then
  if [ -z "${KAGGLE_USERNAME:-}" ] || [ -z "${KAGGLE_KEY:-}" ]; then
    echo "KAGGLE_USERNAME and KAGGLE_KEY are required when the dataset is not mounted." >&2
    exit 1
  fi

  mkdir -p /root/.kaggle /app/data
  printf '{"username":"%s","key":"%s"}\n' "$KAGGLE_USERNAME" "$KAGGLE_KEY" > /root/.kaggle/kaggle.json
  chmod 600 /root/.kaggle/kaggle.json
  python -m kaggle datasets download -d "${KAGGLE_DATASET:-bhatvikas/movielens-100k-dataset}" -p /app/data
  archive="$(find /app/data -maxdepth 1 -type f -name '*.zip' -print -quit)"
  if [ -z "$archive" ]; then
    echo "Kaggle download did not create a ZIP archive." >&2
    exit 1
  fi
  mkdir -p /app/data/raw
  python - "$archive" <<'PY'
import sys
from zipfile import ZipFile

with ZipFile(sys.argv[1]) as archive:
    archive.extractall("/app/data/raw")
PY
  rm -f "$archive" /root/.kaggle/kaggle.json
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
