"""
ChromaDB vector store. Stores each chunk's vector + text + metadata,
and does nearest-neighbour search. Persists to disk so embedding is
a one-time cost, not a per-run cost.
"""

import chromadb
from chromadb.config import Settings

_client = None

def get_collection():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path="chroma_store",
            settings=Settings(anonymized_telemetry=False), # silence the noise
            )
    return _client.get_or_create_collection(
        name="trials",
        metadata={"hnsw:space": "cosine"}, # cosine suits text embeddings
    )

