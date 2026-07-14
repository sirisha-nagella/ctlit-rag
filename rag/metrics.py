"""
Appends one JSON line per query: which model answered, how many tokens it
used, and how long it took. Plain JSONL so it's easy to tail, grep,
or load into analyze_ab.py later - no database needed for this
volume of queries.
"""

import time
import uuid
from pathlib import Path

from rag.jsonl import append_jsonl

LOG_PATH = Path("logs/metrics.jsonl")


def log_query(query, model_key, input_tokens, output_tokens, latency_s):
    """Returns the query_id so feedback.py can link a thumbs up/down to it."""
    query_id = str(uuid.uuid4())
    append_jsonl(LOG_PATH, {
        "query_id": query_id,
        "timestamp": time.time(),
        "query": query,
        "model_key": model_key,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_s": latency_s,
    })
    return query_id
