"""Résumé du Journal Officiel via l'API Mistral (tier gratuit).

Usage :
    python3 summarize.py                     # résumé global du JO (à partir des titres)
    python3 summarize.py "santé"             # résumé thématique (recherche vectorielle + résumé)
    python3 summarize.py -k 15 "écologie"    # nombre de chunks passés au LLM

Clé API : MISTRAL_API_KEY dans le .env (générée sur https://console.mistral.ai,
plan gratuit « Experiment »).
"""

import glob
import json
import os
import sys

import requests

from dl_journal import load_env

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")


def get_api_key():
    load_env()
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        sys.exit(
            "MISTRAL_API_KEY manquante dans le .env.\n"
            "Créer une clé (gratuit) sur https://console.mistral.ai → API Keys."
        )
    return key


def call_mistral(api_key, system, user):
    resp = requests.post(
        MISTRAL_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": MISTRAL_MODEL,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        timeout=120,
    )
    if resp.status_code >= 400:
        sys.exit(f"Erreur Mistral {resp.status_code} :\n{resp.text[:1000]}")
    return resp.json()["choices"][0]["message"]["content"]


def latest_day_dir():
    days = sorted(
        d for d in glob.glob(os.path.join(DATA_DIR, "*")) if os.path.isdir(d) and "index" not in d
    )
    if not days:
        sys.exit("Aucune donnée dans data/ — lancer d'abord fetch_texts.py")
    return days[-1]


def summarize_day(api_key):
    """Résumé global du dernier JO téléchargé, à partir des titres du sommaire."""
    day_dir = latest_day_dir()
    date = os.path.basename(day_dir)
    docs = []
    for path in sorted(glob.glob(os.path.join(day_dir, "JORFTEXT*.json"))):
        with open(path) as f:
            d = json.load(f)
        docs.append(f"- [{d.get('nature')}] {d['titre']}")

    system = (
        "Tu es un assistant juridique qui résume le Journal Officiel de la République "
        "française pour un lecteur pressé. Tu réponds en français, de façon structurée."
    )
    user = (
        f"Voici les titres des {len(docs)} textes publiés au JO du {date} :\n\n"
        + "\n".join(docs)
        + "\n\nFais un résumé thématique de ce JO en quelques sections (ex. santé, "
        "nominations, économie...). Pour chaque thème, 1 à 3 phrases sur l'essentiel. "
        "Termine par les 3 textes qui te semblent avoir le plus d'impact pour le grand public."
    )
    print(f"Résumé du JO du {date} ({len(docs)} textes) via {MISTRAL_MODEL}...\n")
    print(call_mistral(api_key, system, user))


def summarize_theme(api_key, query, k):
    """Recherche vectorielle sur le thème puis résumé des chunks retenus."""
    import numpy as np
    from sentence_transformers import SentenceTransformer

    from search import MODEL_NAME, load_index

    embeddings, chunks = load_index()
    model = SentenceTransformer(MODEL_NAME)
    q = model.encode([f"query: {query}"], normalize_embeddings=True)[0]
    top = np.argsort(embeddings @ q)[::-1][:k]

    extraits = []
    for idx in top:
        c = chunks[idx]
        extraits.append(
            f"### {c['doc_id']} [{c.get('nature')}] {c['titre']}\n{c['texte'][:1500]}"
        )

    system = (
        "Tu es un assistant juridique qui analyse des extraits du Journal Officiel "
        "de la République française. Tu réponds en français. Les extraits proviennent "
        "d'une recherche sémantique : certains peuvent être hors sujet — ignore-les."
    )
    user = (
        f"Sujet demandé : « {query} »\n\n"
        f"Voici {len(extraits)} extraits du JO sélectionnés automatiquement :\n\n"
        + "\n\n".join(extraits)
        + "\n\nRésume ce que le JO contient sur ce sujet. Cite l'identifiant JORFTEXT "
        "des textes que tu mentionnes. Si aucun extrait n'est réellement pertinent, dis-le."
    )
    print(f"Recherche « {query} » ({len(extraits)} extraits) → résumé via {MISTRAL_MODEL}...\n")
    print(call_mistral(api_key, system, user))


def main():
    args = sys.argv[1:]
    k = 10
    if "-k" in args:
        i = args.index("-k")
        k = int(args[i + 1])
        del args[i : i + 2]

    api_key = get_api_key()
    if args:
        summarize_theme(api_key, " ".join(args), k)
    else:
        summarize_day(api_key)


if __name__ == "__main__":
    main()
