"""
Turn text into 384-dim vectors with all-MiniLM-L6-v2.
Load the model once (slow), reuse it for every encode (fast).
"""

from sentence_transformers import SentenceTransformer

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def embed(texts):
    """Accepts a string or list of strings; returns a numpy array."""
    return get_model().encode(texts, convert_to_numpy=True)

# self-test: embed one short string and check the shape

if __name__ == "__main__":
    vec = embed("Eligibility criteria for a Hepatits B trial.")
    print("Vector shape:", vec.shape)
    print("First 5 numbers:", vec[:5])

