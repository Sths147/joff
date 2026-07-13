"""MongoDB-backed record of already-downloaded JO editions, keyed by date,
and of per-user reader profiles used to personalize summaries.

Lets pipeline.fetch_latest_jo() skip re-fetching every text and rebuilding
the vector index when the latest published JO has already been processed.

Profiles are keyed by user_id (the Postgres users.id from users_db.py, passed
through as a string) — this module treats it as an opaque key.
"""

from pymongo import MongoClient

from config import MONGO_URI

_client = None


def get_collection(name):
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client["joff"][name]


def find_jo(date):
    """Return the stored JO edition for `date` (an ISO date string), or None."""
    return get_collection("jo_editions").find_one({"_id": date})


def save_jo(date, label, texts):
    """Upsert the JO edition for `date`, keyed by date."""
    get_collection("jo_editions").replace_one(
        {"_id": date}, {"_id": date, "label": label, "texts": texts}, upsert=True
    )


def get_profile(user_id):
    """Return the saved reader bio for `user_id`, or None if none has been set yet."""
    doc = get_collection("profile").find_one({"_id": user_id})
    return doc["bio"] if doc else None


def save_profile(user_id, bio):
    """Upsert the reader profile for `user_id`."""
    get_collection("profile").replace_one(
        {"_id": user_id}, {"_id": user_id, "bio": bio}, upsert=True
    )
