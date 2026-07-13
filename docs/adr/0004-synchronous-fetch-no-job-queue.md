# JO fetch and summarize run synchronously, no job queue

> **Superseded by [ADR 0006](0006-background-thread-fetch.md)** for the `POST /jo/latest`
> fetch specifically, once vectorization grew past gunicorn's worker timeout. Summarize
> (`GET /jo/latest/summary`) is still synchronous, and the reasoning below still applies to it.

"Get the latest JO" runs fetch, text extraction, and vectorization in-process on a single
request (`POST /jo/latest`) and blocks until done, rather than being queued as a background
job with status polling. This is a personal, single-user tool — the complexity of a job queue
and worker isn't worth it for a wait measured in seconds to low minutes; closing the tab
mid-fetch and losing progress is an accepted trade-off.
