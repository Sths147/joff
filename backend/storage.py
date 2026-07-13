"""MongoDB-backed record of already-downloaded JO editions, keyed by date,
and of the single-user reader profile used to personalize summaries.

Lets pipeline.fetch_latest_jo() skip re-fetching every text and rebuilding
the vector index when the latest published JO has already been processed.
"""

from pymongo import MongoClient

from config import MONGO_URI

_client = None

PROFILE_ID = "me"


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


def get_profile():
    """Return the saved reader bio, or None if none has been set yet."""
    doc = get_collection("profile").find_one({"_id": PROFILE_ID})
    return doc["bio"] if doc else None


def save_profile(bio):
    """Upsert the single reader profile."""
    get_collection("profile").replace_one(
        {"_id": PROFILE_ID}, {"_id": PROFILE_ID, "bio": bio}, upsert=True
    )
