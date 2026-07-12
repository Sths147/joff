# JO fetch and summarize run synchronously, no job queue

"Get the latest JO" runs fetch, text extraction, and vectorization in-process on a single
request (`POST /jo/latest`) and blocks until done, rather than being queued as a background
job with status polling. This is a personal, single-user tool — the complexity of a job queue
and worker isn't worth it for a wait measured in seconds to low minutes; closing the tab
mid-fetch and losing progress is an accepted trade-off.
