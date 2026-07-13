from unittest.mock import MagicMock, patch

import storage


def test_find_jo_queries_by_date_id():
    storage._client = None
    fake_collection = MagicMock()
    fake_collection.find_one.return_value = {"_id": "2026-07-08", "label": "JORF n°0158"}
    with patch("storage.MongoClient", return_value={"joff": {"jo_editions": fake_collection}}):
        result = storage.find_jo("2026-07-08")
    fake_collection.find_one.assert_called_once_with({"_id": "2026-07-08"})
    assert result == {"_id": "2026-07-08", "label": "JORF n°0158"}
    storage._client = None


def test_get_profile_returns_bio_when_set():
    storage._client = None
    fake_collection = MagicMock()
    fake_collection.find_one.return_value = {"_id": "user-1", "bio": "Lawyer in Lyon"}
    with patch("storage.MongoClient", return_value={"joff": {"profile": fake_collection}}):
        result = storage.get_profile("user-1")
    fake_collection.find_one.assert_called_once_with({"_id": "user-1"})
    assert result == "Lawyer in Lyon"
    storage._client = None


def test_get_profile_returns_none_when_unset():
    storage._client = None
    fake_collection = MagicMock()
    fake_collection.find_one.return_value = None
    with patch("storage.MongoClient", return_value={"joff": {"profile": fake_collection}}):
        result = storage.get_profile("user-1")
    assert result is None
    storage._client = None


def test_save_profile_upserts_by_user_id():
    storage._client = None
    fake_collection = MagicMock()
    with patch("storage.MongoClient", return_value={"joff": {"profile": fake_collection}}):
        storage.save_profile("user-1", "Lawyer in Lyon")
    fake_collection.replace_one.assert_called_once_with(
        {"_id": "user-1"}, {"_id": "user-1", "bio": "Lawyer in Lyon"}, upsert=True
    )
    storage._client = None


def test_save_jo_upserts_by_date_id():
    storage._client = None
    fake_collection = MagicMock()
    with patch("storage.MongoClient", return_value={"joff": {"jo_editions": fake_collection}}):
        storage.save_jo("2026-07-08", "JORF n°0158", [{"id": "JORFTEXT1"}])
    fake_collection.replace_one.assert_called_once_with(
        {"_id": "2026-07-08"},
        {"_id": "2026-07-08", "label": "JORF n°0158", "texts": [{"id": "JORFTEXT1"}]},
        upsert=True,
    )
    storage._client = None
