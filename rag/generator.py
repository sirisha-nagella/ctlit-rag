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


def _build_prompt(query, chunks):
    """chunks: list of context strings retrieved from the vector store."""
    context = "\n\n".join(chunks)
    return (
        f"Trial context:\n{context}\n\n"
        f"Question: {query}\n\n"
        f"Answer using only the context above:"
    )


def _generate_ollama(query, chunks):
    prompt = _build_prompt(query, chunks)

    start = time.time()
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        options={"temperature": 0.2},  # low temp = faithful, less invention
    )
    latency_s = time.time() - start

    answer = response["message"]["content"].strip()
    input_tokens = response.get("prompt_eval_count", 0)
    output_tokens = response.get("eval_count", 0)
    query_id = log_query(query, "ollama", input_tokens, output_tokens, latency_s)

    return answer, "ollama", query_id


def _generate_bedrock(query, chunks):
    prompt = _build_prompt(query, chunks)

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
    """Returns (answer, model_key, query_id) - same shape for either backend."""
    if LLM_BACKEND == "bedrock":
        return _generate_bedrock(query, chunks)
    return _generate_ollama(query, chunks)
