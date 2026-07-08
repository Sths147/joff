"""Récupère le texte intégral des textes du JO du jour via POST /consult/jorf.

Usage :
    python3 fetch_texts.py                # textes du JO du jour
    python3 fetch_texts.py 2026-07-01     # JO d'une date donnée
    python3 fetch_texts.py --last         # dernier JO paru
    python3 fetch_texts.py --limit 5      # ne récupérer que les N premiers (test)

Sortie : data/<date>/JORFTEXT....json (un fichier par texte, avec le texte brut extrait).
"""

import datetime
import json
import os
import re
import sys
import time
from html.parser import HTMLParser

from dl_journal import (
    extract_texts,
    get_jo_container,
    get_token,
    init_urls,
    load_credentials,
    api_post,
)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def html_to_text(html):
    parser = _TextExtractor()
    parser.feed(html)
    text = "".join(parser.parts)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_plain_text(node, out=None):
    """Collecte récursivement les champs de contenu (HTML) de la réponse /consult/jorf."""
    if out is None:
        out = []
    if isinstance(node, dict):
        for key in ("content", "texteHtml", "texte"):
            value = node.get(key)
            if isinstance(value, str) and value.strip():
                out.append(html_to_text(value))
        for value in node.values():
            if isinstance(value, (dict, list)):
                extract_plain_text(value, out)
    elif isinstance(node, list):
        for item in node:
            extract_plain_text(item, out)
    return out


def fetch_text(token, text_id):
    return api_post(token, "/consult/jorf", {"textCid": text_id})


def main():
    args = sys.argv[1:]
    date = datetime.date.today()
    limit = None
    if "--limit" in args:
        i = args.index("--limit")
        limit = int(args[i + 1])
        del args[i : i + 2]
    if "--last" in args:
        date = None
    elif args:
        date = datetime.date.fromisoformat(args[0])

    client_id, client_secret = load_credentials()
    init_urls()
    token = get_token(client_id, client_secret)

    data, label = get_jo_container(token, date)
    texts = extract_texts(data)
    if not texts:
        sys.exit(f"Aucun texte dans le sommaire pour {label}.")
    if limit:
        texts = texts[:limit]

    day_dir = os.path.join(DATA_DIR, str(date) if date else label.replace("/", "-"))
    os.makedirs(day_dir, exist_ok=True)

    print(f"{label} : récupération de {len(texts)} textes vers {day_dir}")
    for i, t in enumerate(texts, 1):
        out_path = os.path.join(day_dir, f"{t['id']}.json")
        if os.path.exists(out_path):
            print(f"{i:3}/{len(texts)} {t['id']} (déjà présent)")
            continue
        try:
            raw = fetch_text(token, t["id"])
        except SystemExit as e:
            print(f"{i:3}/{len(texts)} {t['id']} ERREUR : {e}")
            continue
        plain = "\n\n".join(extract_plain_text(raw))
        record = {
            "id": t["id"],
            "titre": t["titre"],
            "nature": t.get("nature"),
            "date_jo": str(date) if date else label,
            "texte": plain,
        }
        with open(out_path, "w") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        print(f"{i:3}/{len(texts)} {t['id']} ({len(plain)} caractères)")
        time.sleep(0.2)  # rester sous les quotas PISTE

    print(f"\nTerminé. Fichiers dans {day_dir}")


if __name__ == "__main__":
    main()
