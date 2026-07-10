
"""
Appends one JSON line per feedback click: which query_id it's for,
and whether it was thumbs up or down. Separate file from metrics. jsonl
so query logging and user feedback don't collide on writes, and so
you can wipe/reset one without touching the other.
"""

import json
import time
from pathlib import Path

FEEDBACK_PATH = Path("logs/feedback.jsonl")


def log_feedback(query_id, rating):
    """rating: 'up' or 'down'. Appends a feedback record linked to query_id."""
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "query_id": query_id,
        "timestamp": time.time(),
        "rating": rating,
    }

    with open(FEEDBACK_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
