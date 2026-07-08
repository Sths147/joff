"""Recherche sémantique dans l'index construit par vectorize.py.

Usage :
    python3 search.py "prix des médicaments remboursés"
    python3 search.py -k 10 "nomination préfet"
"""

import json
import os
import sys

import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_DIR = os.path.join(BASE_DIR, "data", "index")
MODEL_NAME = "intfloat/multilingual-e5-small"


def load_index():
    emb_path = os.path.join(INDEX_DIR, "embeddings.npy")
    chunks_path = os.path.join(INDEX_DIR, "chunks.jsonl")
    if not (os.path.exists(emb_path) and os.path.exists(chunks_path)):
        raise SystemExit("Index absent — lancer d'abord vectorize.py")
    embeddings = np.load(emb_path)
    with open(chunks_path) as f:
        chunks = [json.loads(line) for line in f]
    return embeddings, chunks


def main():
    args = sys.argv[1:]
    k = 5
    if "-k" in args:
        i = args.index("-k")
        k = int(args[i + 1])
        del args[i : i + 2]
    if not args:
        raise SystemExit('Usage : python3 search.py [-k N] "votre requête"')
    query = " ".join(args)

    embeddings, chunks = load_index()
    model = SentenceTransformer(MODEL_NAME)
    # e5 attend le préfixe "query: " pour les requêtes
    q = model.encode([f"query: {query}"], normalize_embeddings=True)[0]

    scores = embeddings @ q  # cosinus (vecteurs normalisés)
    top = np.argsort(scores)[::-1][:k]

    print(f'Requête : "{query}"\n')
    for rank, idx in enumerate(top, 1):
        c = chunks[idx]
        extrait = c["texte"][:300].replace("\n", " ")
        print(f"{rank}. [{scores[idx]:.3f}] [{c.get('nature')}] {c['titre'][:110]}")
        print(f"   {c['doc_id']} ({c.get('date_jo')})")
        print(f"   {extrait}...\n")


if __name__ == "__main__":
    main()
