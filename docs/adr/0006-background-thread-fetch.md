# JO fetch runs in a background thread, not the request

`POST /jo/latest` now starts `fetch_latest_jo()` in a background thread and returns
immediately with a status (`idle`/`running`/`done`/`error`); the client polls
`GET /jo/latest/status` for the result. This reopens [ADR 0004](0004-synchronous-fetch-no-job-queue.md)'s
"blocks until done" decision for this one endpoint: vectorization time grows with the size of
the index (all chunks are re-embedded from scratch each run — see `vectorize.py`), and once it
exceeded gunicorn's default 30s worker timeout, both the daily cron trigger and manual
"Get latest JO" clicks started failing outright, logged misleadingly as an OOM kill.

A full job queue (Celery/RQ + broker) was rejected as overkill for a personal, single-user
tool per ADR 0004's original reasoning — this only needed the request to stop blocking, not
durable/distributed job execution. So instead: one global in-memory job slot
(`backend/jobs.py`), no persistence across process restarts, no queue. A second trigger while
one is in flight (e.g. the cron firing while the fetch button is also clicked) observes the
same run rather than starting a duplicate. Losing an in-progress job on a server restart is
an accepted trade-off, same spirit as ADR 0004.

`GET /jo/latest/summary` stays synchronous — it reads pre-built index data and returns in
seconds, so ADR 0004's original reasoning still applies to it unchanged.
