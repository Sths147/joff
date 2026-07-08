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

import requests

# Set by init_urls() after reading the .env (PISTE_ENV=sandbox for the test environment)
OAUTH_URL = None
API_BASE = None


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
        sys.exit(
            "Missing credentials: set PISTE_CLIENT_ID and PISTE_CLIENT_SECRET\n"
            "(environment variables or .env file — see .env.example).\n"
            "They are generated on https://piste.gouv.fr after subscribing to the Légifrance API."
        )
    return client_id, client_secret


def get_token(client_id, client_secret):
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
        sys.exit(
            f"OAuth error {resp.status_code}:\n{resp.text[:2000]}\n\n"
            "Check that the client_id/client_secret match the target environment "
            f"({OAUTH_URL}) and that the application is subscribed to the Légifrance API."
        )
    return resp.json()["access_token"]


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
        sys.exit(f"API error {resp.status_code} on {endpoint}:\n{resp.text[:2000]}")
    return resp.json()


def get_jo_container(token, date=None):
    """Fetch the JORF container (table of contents) for a date, or the latest published one."""
    if date is not None:
        millis = int(
            datetime.datetime.combine(date, datetime.time(12)).timestamp() * 1000
        )
        return api_post(token, "/consult/jorfCont", {"date": millis}), str(date)

    # Latest published JO: list the most recent containers then load the first one
    last = api_post(token, "/consult/lastNJo", {"nbElement": 1})
    containers = last.get("containers") or []
    if not containers:
        sys.exit(f"No JO container returned by /consult/lastNJo:\n{json.dumps(last)[:1000]}")
    cont = containers[0]
    cont_id = cont.get("id")
    label = cont.get("titre") or cont_id
    return api_post(token, "/consult/jorfCont", {"id": cont_id}), label


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

    client_id, client_secret = load_credentials()
    init_urls()
    print(f"Getting OAuth token ({OAUTH_URL})...")
    token = get_token(client_id, client_secret)

    print(f"Fetching the JO ({'latest published' if date is None else date})...")
    data, label = get_jo_container(token, date)

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
