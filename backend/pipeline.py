"""Orchestration functions used by the Flask API (backend/app.py).

Each function wraps the existing CLI scripts' library functions, always
operating on the latest published JO (never a specific date) and reading from
already-vectorized data on disk for summaries — see ADR 0004.
"""

import time

from psycopg2.errors import UniqueViolation

import storage
import users_db
from auth import hash_password, verify_password
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
from summarize import get_api_key, summarize_day, summarize_personalized, summarize_theme
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


def personalized_summary(user_id):
    """Topics from the latest JO relevant to the reader profile saved for `user_id`.

    Returns a list of {"title", "facts", "details"} dicts — see
    summarize.summarize_personalized.
    """
    bio = storage.get_profile(user_id)
    if not bio or not bio.strip():
        raise PipelineError(
            "No profile set — add a bio on the Profile page first.", status=400
        )
    api_key = get_api_key()
    return summarize_personalized(api_key, bio)


def get_profile(user_id):
    return storage.get_profile(user_id) or ""


def save_profile(user_id, bio):
    storage.save_profile(user_id, bio)
    return bio


def _normalize_email(email):
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        raise PipelineError("Invalid email address.", status=400)
    return email


def register_user(email, password):
    """Create a new account and return (user_id, normalized_email).

    Raises PipelineError(409) on a duplicate email, PipelineError(400) on
    invalid input.
    """
    email = _normalize_email(email)
    if not password or len(password) < 8:
        raise PipelineError("Password must be at least 8 characters.", status=400)
    try:
        user_id = users_db.create_user(email, hash_password(password))
    except UniqueViolation:
        raise PipelineError("An account with this email already exists.", status=409)
    return user_id, email


def login_user(email, password):
    """Verify credentials and return (user_id, normalized_email).

    Raises PipelineError(429) if the account is locked out from too many
    recent failed attempts, PipelineError(401) on unknown email or wrong
    password.
    """
    email = _normalize_email(email)
    user = users_db.find_user_by_email(email)
    if user and user["locked_until"] and user["locked_until"].timestamp() > time.time():
        raise PipelineError("Too many attempts — try again later.", status=429)
    if not user or not verify_password(password, user["password_hash"]):
        if user:
            users_db.record_failed_login(email)
        raise PipelineError("Invalid email or password.", status=401)
    users_db.reset_failed_attempts(email)
    return user["id"], email
