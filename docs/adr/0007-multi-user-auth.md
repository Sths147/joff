# Multi-user auth: httpOnly session cookies, nginx as the sole public entry point

The app moved from a localhost-only personal tool ([ADR 0005](0005-no-auth-localhost-only.md))
to a publicly reachable, multi-user server: every visitor now registers/logs in and gets their
own profile, and every route requires a session — closing off the unauthenticated access to
billed PISTE/Mistral API calls that ADR 0005 relied on staying off the public internet to avoid.

The session token is a JWT kept in an httpOnly cookie rather than `localStorage`, so a single
XSS bug can't exfiltrate it. That requires the frontend and backend to be same-origin (a
cross-origin cookie needs `SameSite=None; Secure`, i.e. HTTPS everywhere including local dev),
so the existing `frontend` nginx container was extended into the app's single public entry
point: it terminates TLS (self-signed for now — there's no domain yet; swapping in a real
Let's Encrypt-issued certificate later is a manual file swap, a trade made in exchange for not
adding a dedicated proxy like Caddy) and proxies `/jo`, `/profile`, `/auth` through to
`backend:5000`, which is no longer reachable directly from the host. The same trick is used in
local dev via a Vite dev-server proxy, so there's exactly one cookie/CORS story in both
environments.

Sessions are stateless (plain JWT, no server-side revocation table), with a 7-day expiry —
logout clears the cookie client-side; a stolen cookie remains valid until it naturally expires,
capped at a week. A revocation table was considered and declined as more complexity than
justified at this scale. Login has basic brute-force protection: 5 failed attempts locks the
account for 15 minutes, tracked in Postgres (not IP-based, and not in-memory, so it survives
restarts and stays correct regardless of worker count).

User accounts (email + password hash, plus the lockout counters above) live in a new
PostgreSQL database, separate from the existing MongoDB (which keeps `jo_editions` and,
now user-scoped instead of the single hardcoded `"me"` record, `profile`) — a relational store
is the better fit for the uniqueness/lockout state an accounts table needs. Registration is open
self-signup; email verification and password reset are both deliberately deferred — neither
capability (sending email) exists anywhere in this codebase yet, and building one hastily to
unblock this change wasn't worth it.

The one operational wrinkle this created: the daily cron job (see
[ADR 0006](0006-background-thread-fetch.md)) used to trigger `POST /jo/latest` anonymously.
Since that route now requires a session too, the cron container instead sends a shared
`X-Cron-Token` header (checked in `backend/auth.py`'s `require_auth_or_cron`) — acceptable
because that call only ever reaches `backend:5000` directly over the internal Docker network,
never through nginx, so it was never internet-reachable in the first place.
