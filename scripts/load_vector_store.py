"""
Read saved trials -> embed -> load into ChromaDB.
Run from project root: python -m scripts.load_vector_store
"""

import json
from pathlib import Path

from chunking import trial_to_chunks
from rag.embedding_model import embed
from rag.vector_store import get_collection

TRIALS_DIR = Path("data/trials")

def main():

    # 1. build all chunks from saved trials
    chunks = []
    for path in sorted(TRIALS_DIR.glob("*.json")):
        study = json.loads(path.read_text())
        chunks.extend(trial_to_chunks(study))
    print(f"Built {len(chunks)} chunks.")

    # 2. pull the pieces apart for Chroma
    ids = [c["id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    # 3. embed all texts in one batch
    embeddings = embed(texts)
    print(f"Embedded {len(embeddings)} chunks -> {embeddings.shape}")

    # 4. upsert into the store (stable IDs -> re-running is idempotent)
    collection = get_collection()
    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
    )
    print(f"Store now holds {collection.count()} chunks.")

if __name__ == "__main__":
    main()

