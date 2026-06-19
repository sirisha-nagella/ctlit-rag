"""
Semantic search over the trial vector store.
Run from project root: python -m scripts.search
"""

from rag.embedding_model import embed
from rag.vector_store import get_collection

def search(query, k=3):
    """Return the K chunks closest in meaning to the query."""
    query_vec = embed(query)
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_vec.tolist()],
        n_results=k,
    )

    # unpack chroma's nested response into simple tuples
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]
    return list(zip(docs, metas, dists))


if __name__ == "__main__":
    #query = "trials about hepatitis B treatment"
    #query = "immune system therapy for liver infection"
    query = "hepatitis C treatment with sofosbuvir"
    print(f"Query: {query}\n")

    for doc, meta, dist in search(query, k=6):
        source = meta["source"]                        # clinical_trial | literature
        ref = meta.get("nct_id") or meta.get("pmid")   # Whichever ID it has
        print(f"[{dist:.3f}] {source:14} {ref}")
        print(f"   {doc[:130]}...\n")

