"""Vectorize the JO texts fetched by fetch_texts.py.

Splits each text into chunks (~1200 characters), vectorizes them with a local
multilingual embedding model (intfloat/multilingual-e5-small), and stores the
index in data/index/ (embeddings.npy + chunks.jsonl).

Usage:
    python3 vectorize.py          # (re)builds the index from all of data/
"""

import glob
import json
import os

import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
INDEX_DIR = os.path.join(DATA_DIR, "index")
MODEL_NAME = "intfloat/multilingual-e5-small"
CHUNK_SIZE = 1200  # characters
CHUNK_OVERLAP = 200


def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split into pieces of roughly `size` characters, breaking on paragraphs."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, current = [], ""
    for p in paragraphs:
        if current and len(current) + len(p) > size:
            chunks.append(current)
            current = current[-overlap:] + "\n\n" if overlap else ""
        current += p + "\n\n"
    if current.strip():
        chunks.append(current.strip())
    # single paragraph longer than size: hard split
    final = []
    for c in chunks:
        while len(c) > size * 2:
            final.append(c[:size])
            c = c[size - overlap :]
        final.append(c)
    return final


def load_documents():
    docs = []
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "*", "JORFTEXT*.json"))):
        with open(path) as f:
            docs.append(json.load(f))
    return docs


def main():
    docs = load_documents()
    if not docs:
        raise SystemExit("No text in data/ — run fetch_texts.py first")

    chunks = []
    for doc in docs:
        text = doc.get("texte") or ""
        if not text.strip():
            continue
        for i, piece in enumerate(chunk_text(text)):
            chunks.append(
                {
                    "id": f"{doc['id']}#{i}",
                    "doc_id": doc["id"],
                    "titre": doc["titre"],
                    "nature": doc.get("nature"),
                    "date_jo": doc.get("date_jo"),
                    "texte": piece,
                }
            )

    print(f"{len(docs)} documents → {len(chunks)} chunks")
    print(f"Loading model {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    # e5 expects the "passage: " prefix for indexed documents
    inputs = [f"passage: {c['titre']}\n{c['texte']}" for c in chunks]
    embeddings = model.encode(
        inputs, normalize_embeddings=True, show_progress_bar=True, batch_size=32
    )

    os.makedirs(INDEX_DIR, exist_ok=True)
    np.save(os.path.join(INDEX_DIR, "embeddings.npy"), embeddings.astype(np.float32))
    with open(os.path.join(INDEX_DIR, "chunks.jsonl"), "w") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"Index written to {INDEX_DIR} ({embeddings.shape[0]} vectors, dim {embeddings.shape[1]})")


if __name__ == "__main__":
    main()
