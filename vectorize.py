"""Vectorise les textes du JO récupérés par fetch_texts.py.

Découpe chaque texte en morceaux (~1200 caractères), les vectorise avec un
modèle d'embeddings multilingue local (intfloat/multilingual-e5-small), et
stocke l'index dans data/index/ (embeddings.npy + chunks.jsonl).

Usage :
    python3 vectorize.py          # (re)construit l'index depuis tout data/
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
CHUNK_SIZE = 1200  # caractères
CHUNK_OVERLAP = 200


def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Découpe en morceaux d'environ `size` caractères, en coupant sur les paragraphes."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, current = [], ""
    for p in paragraphs:
        if current and len(current) + len(p) > size:
            chunks.append(current)
            current = current[-overlap:] + "\n\n" if overlap else ""
        current += p + "\n\n"
    if current.strip():
        chunks.append(current.strip())
    # paragraphe unique plus long que size : découpe brute
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
        raise SystemExit("Aucun texte dans data/ — lancer d'abord fetch_texts.py")

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
    print(f"Chargement du modèle {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    # e5 attend le préfixe "passage: " pour les documents indexés
    inputs = [f"passage: {c['titre']}\n{c['texte']}" for c in chunks]
    embeddings = model.encode(
        inputs, normalize_embeddings=True, show_progress_bar=True, batch_size=32
    )

    os.makedirs(INDEX_DIR, exist_ok=True)
    np.save(os.path.join(INDEX_DIR, "embeddings.npy"), embeddings.astype(np.float32))
    with open(os.path.join(INDEX_DIR, "chunks.jsonl"), "w") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"Index écrit dans {INDEX_DIR} ({embeddings.shape[0]} vecteurs, dim {embeddings.shape[1]})")


if __name__ == "__main__":
    main()
