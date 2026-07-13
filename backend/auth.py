"""Password hashing, session-cookie issuance/verification, and the auth guard
used by app.py.

Sessions are a single HS256 JWT stored in an httpOnly cookie (see
set_session_cookie/clear_session_cookie) — no server-side revocation table.
Logging out clears the cookie client-side; a copied/stolen cookie remains
valid until it naturally expires. TOKEN_TTL_SECONDS caps that window instead.
"""

import hmac
import time
from functools import wraps

import jwt
from flask import g, request
from werkzeug.security import check_password_hash, generate_password_hash

from config import COOKIE_SECURE, CRON_TOKEN, JWT_SECRET
from errors import PipelineError

SESSION_COOKIE_NAME = "joff_session"
TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password, password_hash):
    return check_password_hash(password_hash, password)


def _secret():
    if not JWT_SECRET:
        raise PipelineError(
            "JWT_SECRET missing from the .env — see .env.example.\n"
            "Generate one with: openssl rand -hex 32"
        )
    return JWT_SECRET


def issue_token(user_id):
    """Return a signed session JWT for `user_id` (the Postgres users.id)."""
    payload = {"sub": str(user_id), "exp": int(time.time()) + TOKEN_TTL_SECONDS}
    return jwt.encode(payload, _secret(), algorithm="HS256")


def _decode(token):
    try:
        payload = jwt.decode(token, _secret(), algorithms=["HS256"])
    except jwt.PyJWTError:
        raise PipelineError("Invalid or expired session.", status=401)
    return payload["sub"]


def set_session_cookie(response, token):
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=TOKEN_TTL_SECONDS,
        httponly=True,
        samesite="Lax",
        secure=COOKIE_SECURE,
        path="/",
    )


def clear_session_cookie(response):
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")


def require_auth(fn):
    """Route decorator: rejects requests with no/invalid session cookie,
    otherwise stashes the user id on flask.g.user_id for the handler."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.cookies.get(SESSION_COOKIE_NAME)
        if not token:
            raise PipelineError("Not logged in.", status=401)
        g.user_id = _decode(token)
        return fn(*args, **kwargs)

    return wrapper


def require_auth_or_cron(fn):
    """Like require_auth, but also accepts the shared X-Cron-Token header
    (see config.CRON_TOKEN) in place of a user session — used only for
    POST /jo/latest, which the cron container triggers with no logged-in user."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        cron_token = request.headers.get("X-Cron-Token")
        if CRON_TOKEN and cron_token and hmac.compare_digest(cron_token, CRON_TOKEN):
            g.user_id = None
            return fn(*args, **kwargs)
        return require_auth(fn)(*args, **kwargs)

    return wrapper
