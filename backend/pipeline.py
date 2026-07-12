"""Orchestration functions used by the Flask API (backend/app.py).

Each function wraps the existing CLI scripts' library functions, always
operating on the latest published JO (never a specific date) and reading from
already-vectorized data on disk for summaries — see ADR 0004.
"""

import storage
from dl_journal import (
    extract_jo_date,
    extract_texts,
    get_jo_container,
    get_token,
    init_urls,
    load_credentials,
)
from errors import PipelineError
from fetch_texts import fetch_all_texts
from summarize import get_api_key, summarize_day, summarize_theme
from vectorize import build_index


def fetch_latest_jo():
    """Fetch the latest published JO's full texts and rebuild the vector index,
    unless that edition (keyed by its publication date) is already in storage.

    Returns {"label": ..., "texts": [{"id", "titre", "nature"}, ...]}.
    """
    client_id, client_secret = load_credentials()
    init_urls()
    token = get_token(client_id, client_secret)

    data, label = get_jo_container(token, date=None)
    date = extract_jo_date(data)

    cached = storage.find_jo(date) if date else None
    if cached:
        return {"label": cached["label"], "texts": cached["texts"]}

    texts = extract_texts(data)
    if not texts:
        raise PipelineError(f"No text in the table of contents for {label}.", status=502)

    fetch_all_texts(token, texts, label, date=None)
    build_index()
    if date:
        storage.save_jo(date, label, texts)
    return {"label": label, "texts": texts}


def global_summary():
    api_key = get_api_key()
    return summarize_day(api_key)


def thematic_summary(topic, k=10, min_score=0.83):
    if not topic or not topic.strip():
        raise PipelineError("Missing topic for thematic summary.", status=400)
    api_key = get_api_key()
    return summarize_theme(api_key, topic, k, min_score)
