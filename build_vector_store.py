import json
import faiss
import numpy as np

embeddings = np.load("embeddings.npy")

with open("chunks.json") as f:
    chunks = json.load(f)

dim = embeddings.shape[1]

index = faiss.IndexFlatL2(dim)
index.add(embeddings)

faiss.write_index(index, "vector_store.faiss")
