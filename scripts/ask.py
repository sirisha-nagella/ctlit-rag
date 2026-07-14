
"""
Full RAG loop with confidence gating.
Run from project root: python3 -m scripts.ask
"""

from scripts.search import search
from rag.generator import generate_answer

# If even the closest chunk is farther than this, we don't trust the match.
# Tuned from observed distances: tight ~0.17, good ~0.28, weak/off-topic > 0.5
DISTANCE_THRESHOLD = 0.50

NO_MATCH = (
    "I don't have a trial or paper in my knowledge base that covers "
    "this question well enough to answer it reliably."
)

def ask(query, k=3):
    hits = search(query, k)    #[(doc, meta, dist), ...]

    if not hits:               # nothing in the store matched at all
        return NO_MATCH, [], False, None, None

    best_distance = hits[0][2]  # distance of the closest chunk
    if best_distance > DISTANCE_THRESHOLD:
        return NO_MATCH, hits, False, None, None   # False = not confident


    chunks = [doc for doc, meta, dist in hits]
    answer, model_key, query_id = generate_answer(query, chunks)
    return answer, hits, True, model_key, query_id     # True = confident

if __name__ == "__main__":
    query = "what hepatitis B trials are there and what do they study?"
    #query = "What are the best insulin treatments for type 2 diabetes?"
    #query = "What cancer immunotherapy trials exist?"
    answer, hits, confident, model_key, query_id = ask(query)

    print(f"Q: {query}\n")
    print(f"A: {answer}\n")
    print(f"Confident: {confident} (best distance: {hits[0][2]:.3f})" if hits else f"Confident: {confident}")
    if model_key:
        print(f"Model: {model_key} (query_id: {query_id})")
    print("Sources:")
    for doc, meta, dist in hits:
        ref = meta.get("nct_id") or meta.get("pmid")
        print(f"  - {ref} ({meta['source']}, {meta['section']}, {dist:.3f})")



