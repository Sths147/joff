from unittest.mock import patch

import pytest

from app import app
from errors import PipelineError


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_post_latest_jo_success(client):
    result = {"label": "JORF n0001", "texts": [{"id": "JORFTEXT1", "titre": "x", "nature": "LOI"}]}
    with patch("app.fetch_latest_jo", return_value=result):
        resp = client.post("/jo/latest")
    assert resp.status_code == 200
    assert resp.get_json() == result


def test_post_latest_jo_upstream_error(client):
    with patch("app.fetch_latest_jo", side_effect=PipelineError("upstream boom", status=502)):
        resp = client.post("/jo/latest")
    assert resp.status_code == 502
    assert resp.get_json() == {"error": "upstream boom"}


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
