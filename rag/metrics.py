"""
Appends one JSON line per query: which model answered, how many tokens it
used, and how long it took. Plain JSNOL so it's easy to tail, grep,
or load into analyze_ab.py later - no database needed for this
volume of queries.
"""

import json
import time
import uuid
from pathlib import Path

LOG_PATH = Path("logs/metrics.jsonl")


def log_query(query, model_key, input_tokens, output_tokens, latency_s):
    """Returns the query_id so feedback.py can link a thumbs up/down to it."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    query_id = str(uuid.uuid4())
    entry = {
        "query_id": query_id,
        "timestamp": time.time(),
        "query": query,
        "model_key": model_key,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_s": latency_s,
    }

    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return query_id


    