"""PostgreSQL-backed account storage (registration, login, brute-force lockout).

Kept separate from storage.py (MongoDB — JO cache + per-user profile): accounts
need the uniqueness/lockout state a relational store fits naturally, whereas
jo_editions/profile are a better fit for Mongo's schemaless documents.

No migration tool — init_schema() is an idempotent CREATE TABLE IF NOT EXISTS,
which is enough for a single table.
"""

import psycopg2
import psycopg2.extras

from config import DATABASE_URL

FAILED_ATTEMPTS_LIMIT = 5
LOCKOUT_MINUTES = 15

_conn = None


def get_connection():
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg2.connect(DATABASE_URL)
        _conn.autocommit = True
    return _conn


def init_schema():
    with get_connection().cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )


def _dict_cursor():
    return get_connection().cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def find_user_by_email(email):
    with _dict_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cur.fetchone()


def find_user_by_id(user_id):
    with _dict_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return cur.fetchone()


def create_user(email, password_hash):
    """Insert a new user and return its id. Raises psycopg2.errors.UniqueViolation
    on a duplicate email (the table's UNIQUE constraint is the source of truth,
    closing the race between an existence check and this insert)."""
    with get_connection().cursor() as cur:
        cur.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
            (email, password_hash),
        )
        return cur.fetchone()[0]


def record_failed_login(email):
    """Increment failed_attempts; lock the account for LOCKOUT_MINUTES once it
    reaches FAILED_ATTEMPTS_LIMIT."""
    with get_connection().cursor() as cur:
        cur.execute(
            """
            UPDATE users
            SET failed_attempts = failed_attempts + 1,
                locked_until = CASE
                    WHEN failed_attempts + 1 >= %s
                    THEN now() + make_interval(mins => %s)
                    ELSE locked_until
                END
            WHERE email = %s
            """,
            (FAILED_ATTEMPTS_LIMIT, LOCKOUT_MINUTES, email),
        )


def reset_failed_attempts(email):
    with get_connection().cursor() as cur:
        cur.execute(
            "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE email = %s",
            (email,),
        )
