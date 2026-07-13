import time
from unittest.mock import patch

import jwt
import pytest
from flask import Flask, g

import auth
from errors import PipelineError


def test_hash_and_verify_password_roundtrip():
    hashed = auth.hash_password("correct horse battery staple")
    assert auth.verify_password("correct horse battery staple", hashed)
    assert not auth.verify_password("wrong password", hashed)


@patch("auth.JWT_SECRET", "test-secret")
def test_issue_token_and_decode_roundtrip():
    token = auth.issue_token(42)
    assert auth._decode(token) == "42"


@patch("auth.JWT_SECRET", None)
def test_issue_token_requires_a_secret():
    with pytest.raises(PipelineError):
        auth.issue_token(1)


@patch("auth.JWT_SECRET", "test-secret")
def test_decode_rejects_garbage_token():
    with pytest.raises(PipelineError):
        auth._decode("not-a-real-token")


@patch("auth.JWT_SECRET", "test-secret")
def test_decode_rejects_expired_token():
    expired = jwt.encode(
        {"sub": "1", "exp": int(time.time()) - 10}, "test-secret", algorithm="HS256"
    )
    with pytest.raises(PipelineError):
        auth._decode(expired)


def _protected_app():
    app = Flask(__name__)

    @app.get("/protected")
    @auth.require_auth
    def protected():
        return {"user_id": g.user_id}

    @app.errorhandler(PipelineError)
    def handle(err):
        return {"error": str(err)}, err.status

    return app


@patch("auth.JWT_SECRET", "test-secret")
def test_require_auth_rejects_missing_cookie():
    with _protected_app().test_client() as client:
        resp = client.get("/protected")
    assert resp.status_code == 401


@patch("auth.JWT_SECRET", "test-secret")
def test_require_auth_accepts_valid_cookie():
    token = auth.issue_token(7)
    with _protected_app().test_client() as client:
        client.set_cookie(auth.SESSION_COOKIE_NAME, token)
        resp = client.get("/protected")
    assert resp.status_code == 200
    assert resp.get_json() == {"user_id": "7"}
