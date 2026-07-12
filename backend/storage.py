"""MongoDB-backed record of already-downloaded JO editions, keyed by date.

Lets pipeline.fetch_latest_jo() skip re-fetching every text and rebuilding
the vector index when the latest published JO has already been processed.
"""

from pymongo import MongoClient

from config import MONGO_URI

_client = None


def get_collection():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client["joff"]["jo_editions"]


def find_jo(date):
    """Return the stored JO edition for `date` (an ISO date string), or None."""
    return get_collection().find_one({"_id": date})


def save_jo(date, label, texts):
    """Upsert the JO edition for `date`, keyed by date."""
    get_collection().replace_one(
        {"_id": date}, {"_id": date, "label": label, "texts": texts}, upsert=True
    )
