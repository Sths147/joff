from unittest.mock import MagicMock, patch

import pytest

# app.py calls users_db.init_schema() at import time — patch the connection out
# before importing so the test suite doesn't need a real Postgres.
with patch("users_db.get_connection", return_value=MagicMock()):
    from app import app

import auth
from errors import PipelineError


@pytest.fixture(autouse=True)
def _jwt_secret():
    with patch("auth.JWT_SECRET", "test-secret"):
        yield


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_cookie(client):
    """Log `client` in as "user-1" by setting a valid session cookie on it."""
    token = auth.issue_token("user-1")
    client.set_cookie(auth.SESSION_COOKIE_NAME, token)


def test_protected_routes_reject_missing_session(client):
    resp = client.get("/jo/latest/status")
    assert resp.status_code == 401


def test_post_register_creates_account_and_sets_session_cookie(client):
    with patch("app.register_user", return_value=(5, "a@b.com")) as mock_register:
        resp = client.post(
            "/auth/register", json={"email": "a@b.com", "password": "longenough"}
        )
    assert resp.status_code == 201
    assert resp.get_json() == {"email": "a@b.com"}
    mock_register.assert_called_once_with("a@b.com", "longenough")
    assert auth.SESSION_COOKIE_NAME in resp.headers.get("Set-Cookie", "")


def test_post_login_sets_session_cookie(client):
    with patch("app.login_user", return_value=(5, "a@b.com")) as mock_login:
        resp = client.post("/auth/login", json={"email": "a@b.com", "password": "longenough"})
    assert resp.status_code == 200
    assert resp.get_json() == {"email": "a@b.com"}
    mock_login.assert_called_once_with("a@b.com", "longenough")
    assert auth.SESSION_COOKIE_NAME in resp.headers.get("Set-Cookie", "")


def test_post_logout_clears_session_cookie(client, auth_cookie):
    resp = client.post("/auth/logout")
    assert resp.status_code == 200
    assert auth.SESSION_COOKIE_NAME in resp.headers.get("Set-Cookie", "")


def test_get_me_returns_the_logged_in_users_email(client, auth_cookie):
    with patch("app.users_db.find_user_by_id", return_value={"id": "user-1", "email": "a@b.com"}):
        resp = client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.get_json() == {"email": "a@b.com"}


def test_get_me_rejects_missing_session(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_post_latest_jo_starts_a_job(client, auth_cookie):
    status = {
        "status": "running",
        "label": None,
        "texts": None,
        "error": None,
        "started_at": 1.0,
        "finished_at": None,
    }
    with patch("app.jobs.start_fetch_latest_jo", return_value=status) as mock_start:
        resp = client.post("/jo/latest")
    assert resp.status_code == 202
    assert resp.get_json() == status
    mock_start.assert_called_once()


def test_get_latest_jo_status_reports_the_job_state(client, auth_cookie):
    status = {
        "status": "done",
        "label": "JORF n0001",
        "texts": [{"id": "JORFTEXT1", "titre": "x", "nature": "LOI"}],
        "error": None,
        "started_at": 1.0,
        "finished_at": 2.0,
    }
    with patch("app.jobs.get_status", return_value=status):
        resp = client.get("/jo/latest/status")
    assert resp.status_code == 200
    assert resp.get_json() == status


def test_get_summary_global_by_default(client, auth_cookie):
    with patch("app.global_summary", return_value="résumé global") as mock_global, patch(
        "app.thematic_summary"
    ) as mock_theme:
        resp = client.get("/jo/latest/summary")
    assert resp.status_code == 200
    assert resp.get_json() == {"summary": "résumé global"}
    mock_global.assert_called_once()
    mock_theme.assert_not_called()


def test_get_summary_thematic_when_topic_given(client, auth_cookie):
    with patch("app.thematic_summary", return_value="résumé thématique") as mock_theme:
        resp = client.get("/jo/latest/summary?topic=health&k=5&min_score=0.9")
    assert resp.status_code == 200
    assert resp.get_json() == {"summary": "résumé thématique"}
    mock_theme.assert_called_once_with("health", 5, 0.9)


def test_get_summary_thematic_uses_defaults(client, auth_cookie):
    with patch("app.thematic_summary", return_value="résumé") as mock_theme:
        resp = client.get("/jo/latest/summary?topic=health")
    assert resp.status_code == 200
    mock_theme.assert_called_once_with("health", 10, 0.83)


def test_get_summary_no_data_yet(client, auth_cookie):
    with patch("app.global_summary", side_effect=PipelineError("No data in data/", status=404)):
        resp = client.get("/jo/latest/summary")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "No data in data/"}


def test_get_summary_below_similarity_floor(client, auth_cookie):
    with patch(
        "app.thematic_summary", side_effect=PipelineError("nothing found", status=422)
    ):
        resp = client.get("/jo/latest/summary?topic=obscure")
    assert resp.status_code == 422


def test_get_summary_personalized_when_requested(client, auth_cookie):
    topics = [{"title": "Santé", "facts": "...", "details": "..."}]
    with patch(
        "app.personalized_summary", return_value=topics
    ) as mock_personalized, patch("app.global_summary") as mock_global:
        resp = client.get("/jo/latest/summary?personalized=1")
    assert resp.status_code == 200
    assert resp.get_json() == {"topics": topics}
    mock_personalized.assert_called_once_with("user-1")
    mock_global.assert_not_called()


def test_get_summary_personalized_without_profile(client, auth_cookie):
    with patch(
        "app.personalized_summary",
        side_effect=PipelineError("No profile set", status=400),
    ):
        resp = client.get("/jo/latest/summary?personalized=1")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "No profile set"}


def test_get_profile_returns_saved_bio(client, auth_cookie):
    with patch("app.get_profile", return_value="Lawyer in Lyon") as mock_get:
        resp = client.get("/profile")
    assert resp.status_code == 200
    assert resp.get_json() == {"bio": "Lawyer in Lyon"}
    mock_get.assert_called_once_with("user-1")


def test_put_profile_saves_bio(client, auth_cookie):
    with patch("app.save_profile", return_value="Lawyer in Lyon") as mock_save:
        resp = client.put("/profile", json={"bio": "Lawyer in Lyon"})
    assert resp.status_code == 200
    assert resp.get_json() == {"bio": "Lawyer in Lyon"}
    mock_save.assert_called_once_with("user-1", "Lawyer in Lyon")


def test_put_profile_defaults_to_empty_bio(client, auth_cookie):
    with patch("app.save_profile", return_value="") as mock_save:
        resp = client.put("/profile", json={})
    assert resp.status_code == 200
    mock_save.assert_called_once_with("user-1", "")
