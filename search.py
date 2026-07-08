"""Semantic search in the index built by vectorize.py.

Usage:
    python3 search.py "price of reimbursed medicines"
    python3 search.py -k 10 "prefect appointment"
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
        raise SystemExit("Index missing — run vectorize.py first")
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
        raise SystemExit('Usage: python3 search.py [-k N] "your query"')
    query = " ".join(args)

    embeddings, chunks = load_index()
    model = SentenceTransformer(MODEL_NAME)
    # e5 expects the "query: " prefix for queries
    q = model.encode([f"query: {query}"], normalize_embeddings=True)[0]

    scores = embeddings @ q  # cosine (normalized vectors)
    top = np.argsort(scores)[::-1][:k]

    print(f'Query: "{query}"\n')
    for rank, idx in enumerate(top, 1):
        c = chunks[idx]
        excerpt = c["texte"][:300].replace("\n", " ")
        print(f"{rank}. [{scores[idx]:.3f}] [{c.get('nature')}] {c['titre'][:110]}")
        print(f"   {c['doc_id']} ({c.get('date_jo')})")
        print(f"   {excerpt}...\n")


if __name__ == "__main__":
    main()
