from unittest.mock import patch

import pytest

from app import app
from errors import PipelineError


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_post_latest_jo_starts_a_job(client):
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


def test_get_latest_jo_status_reports_the_job_state(client):
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


def test_get_summary_global_by_default(client):
    with patch("app.global_summary", return_value="résumé global") as mock_global, patch(
        "app.thematic_summary"
    ) as mock_theme:
        resp = client.get("/jo/latest/summary")
    assert resp.status_code == 200
    assert resp.get_json() == {"summary": "résumé global"}
    mock_global.assert_called_once()
    mock_theme.assert_not_called()


def test_get_summary_thematic_when_topic_given(client):
    with patch("app.thematic_summary", return_value="résumé thématique") as mock_theme:
        resp = client.get("/jo/latest/summary?topic=health&k=5&min_score=0.9")
    assert resp.status_code == 200
    assert resp.get_json() == {"summary": "résumé thématique"}
    mock_theme.assert_called_once_with("health", 5, 0.9)


def test_get_summary_thematic_uses_defaults(client):
    with patch("app.thematic_summary", return_value="résumé") as mock_theme:
        resp = client.get("/jo/latest/summary?topic=health")
    assert resp.status_code == 200
    mock_theme.assert_called_once_with("health", 10, 0.83)


def test_get_summary_no_data_yet(client):
    with patch("app.global_summary", side_effect=PipelineError("No data in data/", status=404)):
        resp = client.get("/jo/latest/summary")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "No data in data/"}


def test_get_summary_below_similarity_floor(client):
    with patch(
        "app.thematic_summary", side_effect=PipelineError("nothing found", status=422)
    ):
        resp = client.get("/jo/latest/summary?topic=obscure")
    assert resp.status_code == 422


def test_get_summary_personalized_when_requested(client):
    with patch(
        "app.personalized_summary", return_value="résumé personnalisé"
    ) as mock_personalized, patch("app.global_summary") as mock_global:
        resp = client.get("/jo/latest/summary?personalized=1")
    assert resp.status_code == 200
    assert resp.get_json() == {"summary": "résumé personnalisé"}
    mock_personalized.assert_called_once()
    mock_global.assert_not_called()


def test_get_summary_personalized_without_profile(client):
    with patch(
        "app.personalized_summary",
        side_effect=PipelineError("No profile set", status=400),
    ):
        resp = client.get("/jo/latest/summary?personalized=1")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "No profile set"}


def test_get_profile_returns_saved_bio(client):
    with patch("app.get_profile", return_value="Lawyer in Lyon"):
        resp = client.get("/profile")
    assert resp.status_code == 200
    assert resp.get_json() == {"bio": "Lawyer in Lyon"}


def test_put_profile_saves_bio(client):
    with patch("app.save_profile", return_value="Lawyer in Lyon") as mock_save:
        resp = client.put("/profile", json={"bio": "Lawyer in Lyon"})
    assert resp.status_code == 200
    assert resp.get_json() == {"bio": "Lawyer in Lyon"}
    mock_save.assert_called_once_with("Lawyer in Lyon")


def test_put_profile_defaults_to_empty_bio(client):
    with patch("app.save_profile", return_value="") as mock_save:
        resp = client.put("/profile", json={})
    assert resp.status_code == 200
    mock_save.assert_called_once_with("")
