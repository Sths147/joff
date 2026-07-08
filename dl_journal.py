"""POC : récupération du Journal Officiel du jour via l'API Legifrance (PISTE).

Usage :
    python3 dl_journal.py                # JO du jour
    python3 dl_journal.py 2026-07-01     # JO d'une date donnée
    python3 dl_journal.py --last         # dernier JO paru (utile si pas de JO aujourd'hui)

Identifiants : variables d'environnement PISTE_CLIENT_ID / PISTE_CLIENT_SECRET,
ou un fichier .env à côté de ce script (PISTE_CLIENT_ID=..., PISTE_CLIENT_SECRET=...).
"""

import datetime
import json
import os
import sys

import requests

# Renseignés par init_urls() après lecture du .env (PISTE_ENV=sandbox pour l'env de test)
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
    """Charge les variables d'un éventuel fichier .env local dans l'environnement."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def load_credentials():
    """Lit les identifiants PISTE depuis l'environnement / le .env local."""
    load_env()
    client_id = os.environ.get("PISTE_CLIENT_ID")
    client_secret = os.environ.get("PISTE_CLIENT_SECRET")
    if not client_id or not client_secret:
        sys.exit(
            "Identifiants manquants : définir PISTE_CLIENT_ID et PISTE_CLIENT_SECRET\n"
            "(variables d'environnement ou fichier .env — voir .env.example).\n"
            "Ils se génèrent sur https://piste.gouv.fr après souscription à l'API Légifrance."
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
            f"Erreur OAuth {resp.status_code} :\n{resp.text[:2000]}\n\n"
            "Vérifier que le client_id/client_secret correspondent bien à l'environnement "
            f"visé ({OAUTH_URL}) et que l'application a souscrit à l'API Légifrance."
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
        sys.exit(f"Erreur API {resp.status_code} sur {endpoint} :\n{resp.text[:2000]}")
    return resp.json()


def get_jo_container(token, date=None):
    """Récupère le conteneur JORF (sommaire) pour une date, ou le dernier paru."""
    if date is not None:
        millis = int(
            datetime.datetime.combine(date, datetime.time(12)).timestamp() * 1000
        )
        return api_post(token, "/consult/jorfCont", {"date": millis}), str(date)

    # Dernier JO paru : on liste les derniers conteneurs puis on charge le premier
    last = api_post(token, "/consult/lastNJo", {"nbElement": 1})
    containers = last.get("containers") or []
    if not containers:
        sys.exit(f"Aucun conteneur JO retourné par /consult/lastNJo :\n{json.dumps(last)[:1000]}")
    cont = containers[0]
    cont_id = cont.get("id")
    label = cont.get("titre") or cont_id
    return api_post(token, "/consult/jorfCont", {"id": cont_id}), label


def extract_texts(node, seen=None, out=None):
    """Parcourt récursivement la réponse et collecte les textes du sommaire (JORFTEXT...)."""
    if seen is None:
        seen, out = set(), []
    if isinstance(node, dict):
        ident = node.get("id") or node.get("cid") or ""
        titre = node.get("titre") or node.get("titreTxt") or node.get("title")
        if isinstance(ident, str) and ident.startswith("JORFTEXT") and titre and ident not in seen:
            seen.add(ident)
            out.append({"id": ident, "titre": titre, "nature": node.get("nature")})
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
    print(f"Obtention du jeton OAuth ({OAUTH_URL})...")
    token = get_token(client_id, client_secret)

    print(f"Récupération du JO ({'dernier paru' if date is None else date})...")
    data, label = get_jo_container(token, date)

    raw_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jo_raw.json")
    with open(raw_path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    texts = extract_texts(data)
    if not texts:
        print(f"Aucun texte trouvé pour {label} (pas de JO ce jour-là ?).")
        print(f"Réponse brute sauvegardée dans {raw_path} — réessayer avec --last.")
        return

    print(f"\n=== {label} — {len(texts)} textes ===\n")
    for i, t in enumerate(texts, 1):
        nature = f" [{t['nature']}]" if t.get("nature") else ""
        print(f"{i:3}.{nature} {t['titre']}")
        print(f"     {t['id']}")
    print(f"\nRéponse brute complète : {raw_path}")


if __name__ == "__main__":
    main()
