from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from psycopg2.errors import UniqueViolation

import auth
from errors import PipelineError
from pipeline import (
    fetch_latest_jo,
    get_profile,
    login_user,
    personalized_summary,
    register_user,
    save_profile,
)


def _patched(**overrides):
    defaults = dict(
        load_credentials=("id", "secret"),
        init_urls=None,
        get_token="token",
        get_jo_container=({"joCont": {"datePubli": 1783468800000}}, "JORF n°0158"),
        extract_texts=[{"id": "JORFTEXT1", "titre": "x", "nature": "LOI"}],
    )
    defaults.update(overrides)
    return defaults


def test_fetch_latest_jo_skips_refetch_when_already_stored():
    p = _patched()
    with patch("pipeline.load_credentials", return_value=p["load_credentials"]), patch(
        "pipeline.init_urls"
    ), patch("pipeline.get_token", return_value=p["get_token"]), patch(
        "pipeline.get_jo_container", return_value=p["get_jo_container"]
    ), patch(
        "pipeline.storage.find_jo",
        return_value={"label": "JORF n°0158", "texts": p["extract_texts"]},
    ) as mock_find, patch(
        "pipeline.fetch_all_texts"
    ) as mock_fetch_all, patch(
        "pipeline.build_index"
    ) as mock_build, patch(
        "pipeline.storage.save_jo"
    ) as mock_save:
        result = fetch_latest_jo()

    mock_find.assert_called_once_with("2026-07-08")
    mock_fetch_all.assert_not_called()
    mock_build.assert_not_called()
    mock_save.assert_not_called()
    assert result == {"label": "JORF n°0158", "texts": p["extract_texts"]}


def test_fetch_latest_jo_fetches_and_stores_when_new():
    p = _patched()
    with patch("pipeline.load_credentials", return_value=p["load_credentials"]), patch(
        "pipeline.init_urls"
    ), patch("pipeline.get_token", return_value=p["get_token"]), patch(
        "pipeline.get_jo_container", return_value=p["get_jo_container"]
    ), patch(
        "pipeline.extract_texts", return_value=p["extract_texts"]
    ), patch(
        "pipeline.storage.find_jo", return_value=None
    ) as mock_find, patch(
        "pipeline.fetch_all_texts"
    ) as mock_fetch_all, patch(
        "pipeline.build_index"
    ) as mock_build, patch(
        "pipeline.storage.save_jo"
    ) as mock_save:
        result = fetch_latest_jo()

    mock_find.assert_called_once_with("2026-07-08")
    mock_fetch_all.assert_called_once()
    mock_build.assert_called_once()
    mock_save.assert_called_once_with("2026-07-08", "JORF n°0158", p["extract_texts"])
    assert result == {"label": "JORF n°0158", "texts": p["extract_texts"]}


def test_personalized_summary_uses_saved_bio():
    with patch("pipeline.storage.get_profile", return_value="Lawyer in Lyon") as mock_get, patch(
        "pipeline.get_api_key", return_value="key"
    ), patch("pipeline.summarize_day", return_value="résumé") as mock_summarize:
        result = personalized_summary("user-1")
    mock_get.assert_called_once_with("user-1")
    mock_summarize.assert_called_once_with("key", "Lawyer in Lyon")
    assert result == "résumé"


def test_personalized_summary_requires_a_profile():
    with patch("pipeline.storage.get_profile", return_value=None):
        with pytest.raises(PipelineError):
            personalized_summary("user-1")


def test_get_profile_defaults_to_empty_string():
    with patch("pipeline.storage.get_profile", return_value=None):
        assert get_profile("user-1") == ""


def test_save_profile_delegates_to_storage():
    with patch("pipeline.storage.save_profile") as mock_save:
        result = save_profile("user-1", "Lawyer in Lyon")
    mock_save.assert_called_once_with("user-1", "Lawyer in Lyon")
    assert result == "Lawyer in Lyon"


def test_register_user_creates_account_with_normalized_email():
    with patch("pipeline.users_db.create_user", return_value=5) as mock_create:
        user_id, email = register_user("Test@Example.com  ", "longenough")
    assert user_id == 5
    assert email == "test@example.com"
    args = mock_create.call_args[0]
    assert args[0] == "test@example.com"
    assert auth.verify_password("longenough", args[1])


def test_register_user_rejects_short_password():
    with pytest.raises(PipelineError):
        register_user("a@b.com", "short")


def test_register_user_rejects_invalid_email():
    with pytest.raises(PipelineError):
        register_user("not-an-email", "longenough")


def test_register_user_rejects_duplicate_email():
    with patch("pipeline.users_db.create_user", side_effect=UniqueViolation()):
        with pytest.raises(PipelineError) as exc_info:
            register_user("a@b.com", "longenough")
    assert exc_info.value.status == 409


def test_login_user_succeeds_with_correct_password():
    hashed = auth.hash_password("longenough")
    user = {"id": 3, "email": "a@b.com", "password_hash": hashed, "locked_until": None}
    with patch("pipeline.users_db.find_user_by_email", return_value=user), patch(
        "pipeline.users_db.reset_failed_attempts"
    ) as mock_reset:
        user_id, email = login_user("A@B.com", "longenough")
    assert (user_id, email) == (3, "a@b.com")
    mock_reset.assert_called_once_with("a@b.com")


def test_login_user_rejects_wrong_password():
    hashed = auth.hash_password("longenough")
    user = {"id": 3, "email": "a@b.com", "password_hash": hashed, "locked_until": None}
    with patch("pipeline.users_db.find_user_by_email", return_value=user), patch(
        "pipeline.users_db.record_failed_login"
    ) as mock_fail:
        with pytest.raises(PipelineError) as exc_info:
            login_user("a@b.com", "wrongpassword")
    assert exc_info.value.status == 401
    mock_fail.assert_called_once_with("a@b.com")


def test_login_user_rejects_unknown_email():
    with patch("pipeline.users_db.find_user_by_email", return_value=None):
        with pytest.raises(PipelineError) as exc_info:
            login_user("nope@b.com", "whatever123")
    assert exc_info.value.status == 401


def test_login_user_rejects_when_locked_out():
    locked_until = datetime.now(timezone.utc) + timedelta(minutes=5)
    user = {"id": 3, "email": "a@b.com", "password_hash": "x", "locked_until": locked_until}
    with patch("pipeline.users_db.find_user_by_email", return_value=user):
        with pytest.raises(PipelineError) as exc_info:
            login_user("a@b.com", "whatever123")
    assert exc_info.value.status == 429
