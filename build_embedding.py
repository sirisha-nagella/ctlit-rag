
import json
from sentence_transformers import SentenceTransformer
import numpy as np

MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)


with open("chunks.json") as f:
    chunks = json.load(f)

texts = [c["text"] for c in chunks]

embeddings = model.encode(texts, show_progress_bar=True)

np.save("embeddings.npy", embeddings)
