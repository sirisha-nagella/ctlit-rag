"""
Grounded generation with a local Ollama model.
Takes the question + retrieved chunks, returns an answer
constrained to the provided context.
"""

import os
import time

import ollama

from rag.llm import router, bedrock_client
from rag.metrics import log_query

LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama") # "ollama" (default) or "bedrock"


MODEL = "llama3.2:3b"  # same local model family as previous project

SYSTEM = (
    "You are a clinical trials assistant. Answer the user's question using "
    "ONLY the trial context provided. If the context does not contain the "
    "answer, say so plainly. Never invent trials, drugs, or numbers."
)


def _generate_ollama(query, chunks):
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

def _generate_bedrock(query, chunks):
    context = "\n\n".join(chunks)
    prompt = (
        f"Trial context:\n{context}\n\n"
        f"Question: {query}\n\n"
        f"Answer using only the context above:"
    )

    model_key, model_id = router.pick_model()

    start = time.time()
    answer, input_tokens, output_tokens = bedrock_client.invoke(
        model_id,
        SYSTEM,
        [{"role": "user", "content": prompt}],
    )
    latency_s = time.time() - start

    query_id = log_query(query, model_key, input_tokens, output_tokens, latency_s)

    return answer, model_key, query_id


def generate_answer(query, chunks):
    """
    Returns (answer, model_key, query_id).
    For the ollama backend, model_key and query_id are None - no
    A/B tracking on the local path, matching pre-v0.7.0 behaviour.
    """

    if LLM_BACKEND == "bedrock":
        return _generate_bedrock(query, chunks)
    
    answer = _generate_ollama(query, chunks)
    return answer, None, None

