from unittest.mock import MagicMock, patch

import psycopg2
import pytest

import users_db


def _connection_returning(fake_cursor):
    fake_conn = MagicMock()
    fake_conn.cursor.return_value.__enter__.return_value = fake_cursor
    return fake_conn


def test_find_user_by_email_found():
    fake_cursor = MagicMock()
    fake_cursor.fetchone.return_value = {"id": 1, "email": "a@b.com"}
    with patch("users_db.get_connection", return_value=_connection_returning(fake_cursor)):
        result = users_db.find_user_by_email("a@b.com")
    fake_cursor.execute.assert_called_once_with(
        "SELECT * FROM users WHERE email = %s", ("a@b.com",)
    )
    assert result == {"id": 1, "email": "a@b.com"}


def test_find_user_by_email_returns_none_when_missing():
    fake_cursor = MagicMock()
    fake_cursor.fetchone.return_value = None
    with patch("users_db.get_connection", return_value=_connection_returning(fake_cursor)):
        result = users_db.find_user_by_email("nope@b.com")
    assert result is None


def test_find_user_by_id_found():
    fake_cursor = MagicMock()
    fake_cursor.fetchone.return_value = {"id": 1, "email": "a@b.com"}
    with patch("users_db.get_connection", return_value=_connection_returning(fake_cursor)):
        result = users_db.find_user_by_id(1)
    fake_cursor.execute.assert_called_once_with("SELECT * FROM users WHERE id = %s", (1,))
    assert result == {"id": 1, "email": "a@b.com"}


def test_create_user_returns_new_id():
    fake_cursor = MagicMock()
    fake_cursor.fetchone.return_value = (42,)
    with patch("users_db.get_connection", return_value=_connection_returning(fake_cursor)):
        result = users_db.create_user("a@b.com", "hashed")
    fake_cursor.execute.assert_called_once_with(
        "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
        ("a@b.com", "hashed"),
    )
    assert result == 42


def test_create_user_raises_on_duplicate_email():
    fake_cursor = MagicMock()
    fake_cursor.execute.side_effect = psycopg2.errors.UniqueViolation()
    with patch("users_db.get_connection", return_value=_connection_returning(fake_cursor)):
        with pytest.raises(psycopg2.errors.UniqueViolation):
            users_db.create_user("a@b.com", "hashed")


def test_record_failed_login_uses_the_configured_limits():
    fake_cursor = MagicMock()
    with patch("users_db.get_connection", return_value=_connection_returning(fake_cursor)):
        users_db.record_failed_login("a@b.com")
    args = fake_cursor.execute.call_args[0]
    assert args[1] == (users_db.FAILED_ATTEMPTS_LIMIT, users_db.LOCKOUT_MINUTES, "a@b.com")


def test_reset_failed_attempts_clears_lockout_state():
    fake_cursor = MagicMock()
    with patch("users_db.get_connection", return_value=_connection_returning(fake_cursor)):
        users_db.reset_failed_attempts("a@b.com")
    fake_cursor.execute.assert_called_once_with(
        "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE email = %s",
        ("a@b.com",),
    )
