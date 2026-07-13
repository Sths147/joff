"""In-process background job tracking for the (slow) JO fetch.

A single global job slot, not a queue: this is a personal, single-user tool
(see ADR 0004/0006) and only one "get latest JO" run is ever meaningful at a
time — a second trigger while one is in flight (e.g. the cron firing while
someone's also clicked "Get latest JO") should just observe the same run
rather than start a duplicate.

fetch_latest_jo() runs in a background thread so POST /jo/latest can return
immediately instead of blocking gunicorn's sync worker past its request
timeout during vectorization, which takes minutes once the index has more
than a handful of editions in it (see ADR 0006).
"""

import threading
import time

from pipeline import fetch_latest_jo

_lock = threading.Lock()
_state = {
    "status": "idle",  # idle | running | done | error
    "label": None,
    "texts": None,
    "error": None,
    "started_at": None,
    "finished_at": None,
}


def start_fetch_latest_jo():
    """Start fetch_latest_jo() in a background thread unless one is already running.

    Returns the resulting state immediately (never blocks on the fetch itself).
    """
    with _lock:
        if _state["status"] != "running":
            _state.update(
                status="running",
                error=None,
                started_at=time.time(),
                finished_at=None,
            )
            threading.Thread(target=_run, daemon=True).start()
        return dict(_state)


def _run():
    try:
        result = fetch_latest_jo()
        with _lock:
            _state.update(
                status="done",
                label=result["label"],
                texts=result["texts"],
                finished_at=time.time(),
            )
    except Exception as e:
        with _lock:
            _state.update(status="error", error=str(e), finished_at=time.time())


def get_status():
    with _lock:
        return dict(_state)
