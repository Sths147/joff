"""Shared path configuration for the pipeline scripts and the Flask API.

DATA_DIR defaults to the repo-root data/ directory (one level up from backend/),
matching where fetched JOs and the vector index have always lived. Override with
JOFF_DATA_DIR when the layout differs, e.g. the Docker volume mount at /app/data.
"""

import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BACKEND_DIR)

DATA_DIR = os.environ.get("JOFF_DATA_DIR", os.path.join(REPO_ROOT, "data"))
INDEX_DIR = os.path.join(DATA_DIR, "index")

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")

# Assembled from parts rather than one interpolated string so the password
# never has to appear literally in docker-compose.yml: docker-compose only
# overrides POSTGRES_HOST (to "postgres", no secret involved) and passes
# POSTGRES_PASSWORD through from backend/.env via env_file: for both the
# backend and postgres services.
_POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
_POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "joff")
DATABASE_URL = os.environ.get(
    "DATABASE_URL", f"postgresql://joff:{_POSTGRES_PASSWORD}@{_POSTGRES_HOST}:5432/joff"
)

JWT_SECRET = os.environ.get("JWT_SECRET")

# Cookies are marked Secure (HTTPS-only) in docker-compose, where nginx always
# terminates TLS (even with a self-signed cert). Left off by default for the
# bare `npm run dev` + directly-run-backend local workflow, which is plain HTTP.
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"

# Shared secret letting the cron container (see cron/crontab) trigger
# POST /jo/latest without a user login — that request only reaches backend:5000
# directly over the internal Docker network, never through nginx, so it's not
# internet-reachable regardless of this token.
CRON_TOKEN = os.environ.get("CRON_TOKEN")
