"""POC: fetch the day's Journal Officiel via the Légifrance API (PISTE).

Usage:
    python3 dl_journal.py                # today's JO
    python3 dl_journal.py 2026-07-01     # JO for a given date
    python3 dl_journal.py --last         # latest published JO (useful if no JO today)

Credentials: PISTE_CLIENT_ID / PISTE_CLIENT_SECRET environment variables,
or a .env file next to this script (PISTE_CLIENT_ID=..., PISTE_CLIENT_SECRET=...).
"""

import datetime
import json
import os
import sys
import time

import requests

from errors import PipelineError

# Set by init_urls() after reading the .env (PISTE_ENV=sandbox for the test environment)
OAUTH_URL = None
API_BASE = None

# client_id -> {"access_token": str, "expires_at": float (time.monotonic())}
_token_cache = {}


def init_urls():
    global OAUTH_URL, API_BASE
    if os.environ.get("PISTE_ENV", "prod") == "sandbox":
        OAUTH_URL = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
        API_BASE = "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"
    else:
        OAUTH_URL = "https://oauth.piste.gouv.fr/api/oauth/token"
        API_BASE = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"


def load_env():
    """Load variables from a local .env file, if any, into the environment."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def load_credentials():
    """Read the PISTE credentials from the environment / the local .env."""
    load_env()
    client_id = os.environ.get("PISTE_CLIENT_ID")
    client_secret = os.environ.get("PISTE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise PipelineError(
            "Missing credentials: set PISTE_CLIENT_ID and PISTE_CLIENT_SECRET\n"
            "(environment variables or .env file — see .env.example).\n"
            "They are generated on https://piste.gouv.fr after subscribing to the Légifrance API."
        )
    return client_id, client_secret


def get_token(client_id, client_secret):
    """Get an OAuth access token, reusing a cached one until shortly before it expires.

    Avoids paying for a fresh OAuth round-trip on every "Fetch" click — most clicks
    just confirm the latest JO is already cached, so the token is the only thing
    otherwise fetched fresh every time.
    """
    cached = _token_cache.get(client_id)
    if cached and cached["expires_at"] > time.monotonic():
        return cached["access_token"]

    resp = requests.post(
        OAUTH_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "openid",
        },
        timeout=30,
    )
    if resp.status_code >= 400:
        raise PipelineError(
            f"OAuth error {resp.status_code}:\n{resp.text[:2000]}\n\n"
            "Check that the client_id/client_secret match the target environment "
            f"({OAUTH_URL}) and that the application is subscribed to the Légifrance API.",
            status=502,
        )
    body = resp.json()
    token = body["access_token"]
    expires_in = body.get("expires_in", 0)
    _token_cache[client_id] = {
        "access_token": token,
        "expires_at": time.monotonic() + expires_in - 30,  # renew a bit early
    }
    return token


def api_post(token, endpoint, payload):
    resp = requests.post(
        f"{API_BASE}{endpoint}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=payload,
        timeout=60,
    )
    if resp.status_code >= 400:
        raise PipelineError(
            f"API error {resp.status_code} on {endpoint}:\n{resp.text[:2000]}", status=502
        )
    return resp.json()


def get_jo_container(token, date=None):
    """Fetch the JORF container (table of contents) for a date, or the latest published one.

    For the latest-published case, /consult/lastNJo's listing entry already *is*
    the full container (same publication date, same texts, verified against
    /consult/jorfCont) — so there's no second call to make here.
    """
    if date is not None:
        millis = int(
            datetime.datetime.combine(date, datetime.time(12)).timestamp() * 1000
        )
        return api_post(token, "/consult/jorfCont", {"date": millis}), str(date)

    last = api_post(token, "/consult/lastNJo", {"nbElement": 1})
    containers = last.get("containers") or []
    if not containers:
        raise PipelineError(
            f"No JO container returned by /consult/lastNJo:\n{json.dumps(last)[:1000]}",
            status=502,
        )
    cont = containers[0]
    label = cont.get("titre") or cont.get("id")
    return cont, label


def extract_jo_date(node):
    """Recursively find the container's publication date (`datePubli`, epoch
    milliseconds) and return it as an ISO date string (e.g. "2026-07-09").

    Used as the canonical id for a JO edition regardless of whether it was
    fetched by explicit date or via --last, whose `label` is a free-form
    string like "JORF n°0159 du 9 juillet 2026" and not safe to use as a key.
    """
    millis = _find_date_publi(node)
    if millis is None:
        return None
    return str(datetime.datetime.fromtimestamp(millis / 1000, tz=datetime.timezone.utc).date())


def _find_date_publi(node):
    if isinstance(node, dict):
        value = node.get("datePubli")
        if isinstance(value, (int, float)):
            return value
        for v in node.values():
            found = _find_date_publi(v)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_date_publi(item)
            if found is not None:
                return found
    return None


def extract_texts(node, seen=None, out=None):
    """Recursively walk the response and collect the table-of-contents texts (JORFTEXT...)."""
    if seen is None:
        seen, out = set(), []
    if isinstance(node, dict):
        ident = node.get("id") or node.get("cid") or ""
        title = node.get("titre") or node.get("titreTxt") or node.get("title")
        if isinstance(ident, str) and ident.startswith("JORFTEXT") and title and ident not in seen:
            seen.add(ident)
            out.append({"id": ident, "titre": title, "nature": node.get("nature")})
        for value in node.values():
            extract_texts(value, seen, out)
    elif isinstance(node, list):
        for item in node:
            extract_texts(item, seen, out)
    return out


def main():
    args = sys.argv[1:]
    date = datetime.date.today()
    if "--last" in args:
        date = None
    elif args:
        date = datetime.date.fromisoformat(args[0])

    try:
        client_id, client_secret = load_credentials()
        init_urls()
        print(f"Getting OAuth token ({OAUTH_URL})...")
        token = get_token(client_id, client_secret)

        print(f"Fetching the JO ({'latest published' if date is None else date})...")
        data, label = get_jo_container(token, date)
    except PipelineError as e:
        sys.exit(str(e))

    raw_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jo_raw.json")
    with open(raw_path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    texts = extract_texts(data)
    if not texts:
        print(f"No text found for {label} (no JO published that day?).")
        print(f"Raw response saved to {raw_path} — retry with --last.")
        return

    print(f"\n=== {label} — {len(texts)} texts ===\n")
    for i, t in enumerate(texts, 1):
        nature = f" [{t['nature']}]" if t.get("nature") else ""
        print(f"{i:3}.{nature} {t['titre']}")
        print(f"     {t['id']}")
    print(f"\nFull raw response: {raw_path}")


if __name__ == "__main__":
    main()
