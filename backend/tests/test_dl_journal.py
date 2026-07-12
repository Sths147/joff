from unittest.mock import MagicMock, patch

import dl_journal
from dl_journal import extract_jo_date, get_token


def test_extract_jo_date_finds_nested_date_publi():
    data = {"items": [{"joCont": {"num": "0158", "datePubli": 1783468800000}}]}
    assert extract_jo_date(data) == "2026-07-08"


def test_extract_jo_date_returns_none_when_absent():
    assert extract_jo_date({"items": []}) is None


def _mock_response(json_body, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body
    return resp


def test_get_token_reuses_cached_token_within_expiry():
    dl_journal._token_cache.clear()
    resp = _mock_response({"access_token": "tok-1", "expires_in": 300})
    with patch("dl_journal.requests.post", return_value=resp) as mock_post:
        first = get_token("id", "secret")
        second = get_token("id", "secret")

    assert first == second == "tok-1"
    mock_post.assert_called_once()


def test_get_token_refetches_once_cached_token_expires():
    dl_journal._token_cache.clear()
    resp = _mock_response({"access_token": "tok-1", "expires_in": 300})
    with patch("dl_journal.requests.post", return_value=resp), patch(
        "dl_journal.time.monotonic", return_value=1000.0
    ):
        get_token("id", "secret")

    resp2 = _mock_response({"access_token": "tok-2", "expires_in": 300})
    with patch("dl_journal.requests.post", return_value=resp2) as mock_post, patch(
        "dl_journal.time.monotonic", return_value=1000.0 + 300
    ):
        token = get_token("id", "secret")

    assert token == "tok-2"
    mock_post.assert_called_once()
