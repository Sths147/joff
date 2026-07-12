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
