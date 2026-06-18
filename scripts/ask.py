"""
Full RAG loop: question -> generate ground answer.
Run from project root: python3 -m scripts.ask
"""

from scripts.search import search
from rag.generator import generate_answer

def ask(query, k=3):
    hits = search(query, k)    #[(doc, meta, dist), ...]
    chunks = [doc for doc, meta, dist in hits]
    answer = generate_answer(query, chunks)
    return answer, hits

if __name__ == "__main__":
    query = "what hepatitis B trials are there and what do they study?"
    answer, hits = ask(query)

    print(f"Q: {query}\n")
    print(f"A: {answer}\n")
    print("Sources:")
    for doc, meta, dist in hits:
        print(f"  -{meta['nct_id']} ({meta['section']}, distance {dist:.3f})")

