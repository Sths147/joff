import threading
import time
from unittest.mock import patch

import pytest

import jobs


@pytest.fixture(autouse=True)
def reset_state():
    jobs._state.update(
        status="idle", label=None, texts=None, error=None, started_at=None, finished_at=None
    )
    yield


def _wait_until_settled(timeout=2):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = jobs.get_status()
        if status["status"] != "running":
            return status
        time.sleep(0.01)
    raise AssertionError("job did not settle in time")


def test_start_fetch_latest_jo_reports_done_on_success():
    result = {"label": "JORF n0001", "texts": [{"id": "JORFTEXT1", "titre": "x", "nature": "LOI"}]}
    with patch("jobs.fetch_latest_jo", return_value=result):
        started = jobs.start_fetch_latest_jo()
        assert started["status"] == "running"
        final = _wait_until_settled()

    assert final["status"] == "done"
    assert final["label"] == result["label"]
    assert final["texts"] == result["texts"]
    assert final["error"] is None


def test_start_fetch_latest_jo_reports_error_on_failure():
    with patch("jobs.fetch_latest_jo", side_effect=RuntimeError("upstream boom")):
        jobs.start_fetch_latest_jo()
        final = _wait_until_settled()

    assert final["status"] == "error"
    assert final["error"] == "upstream boom"


def test_start_fetch_latest_jo_does_not_duplicate_a_running_job():
    release = threading.Event()

    def slow_fetch():
        release.wait(timeout=2)
        return {"label": "JORF n0001", "texts": []}

    with patch("jobs.fetch_latest_jo", side_effect=slow_fetch) as mock_fetch:
        first = jobs.start_fetch_latest_jo()
        second = jobs.start_fetch_latest_jo()
        assert first["status"] == "running"
        assert second["status"] == "running"

        release.set()
        _wait_until_settled()

    mock_fetch.assert_called_once()
