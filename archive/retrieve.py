
import json
from sentence_transformers import SentenceTransformer
import faiss

MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

with open("chunks.json") as f:
    chunks = json.load(f)

index = faiss.read_index("vector_store.faiss")

def retrieve(question, k=5):
    """Return the top 5 results"""
    query_vec = model.encode([question])
    distances, indices = index.search(query_vec, k)
    results = [chunks[i] for i in indices[0]]
    return results

if __name__ == "__main__":
    results = retrieve("what are the eligibility criteria for HIV trials?")
    for r in results:
        print(r["id"], "-", r["text"][:80])
        