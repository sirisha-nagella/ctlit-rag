"""
Grounded generation with a local Ollama model.
Takes the question + retrieved chunks, returns an answer
constrained to the provided context.
"""

import ollama

MODEL = "llama3.1:8b"  # same local model family as previous project

SYSTEM = (
    "You are a clinical trials assistant. Answer the user's question using "
    "ONLY the trial context provided. If the context does not contain the "
    "answer, say so plainly. Never invent trials, drugs, or numbers."
)


def generate_answer(query, chunks):
    """chunks: list of context strings retrieved from the vector store."""
    context = "\n\n".join(chunks)
    prompt = (
        f"Trial context:\n{context}\n\n"
        f"Question: {query}\n\n"
        f"Answer using only the context above:"
    )

    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        options={"temperature": 0.2},  # low temp = faithful, less invention
    )
    return response["message"]["content"].strip()

