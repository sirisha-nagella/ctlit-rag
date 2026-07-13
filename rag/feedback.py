"""
Appends one JSON line per feedback click: which query_id it's for,
and whether it was thumbs up or down. Separate file from metrics.jsonl
so query logging and user feedback don't collide on writes, and so
you can wipe/reset one without touching the other.
"""

import time
from pathlib import Path

from rag.jsonl import append_jsonl

FEEDBACK_PATH = Path("logs/feedback.jsonl")


def log_feedback(query_id, rating):
    """rating: 'up' or 'down'. Appends a feedback record linked to query_id."""
    append_jsonl(FEEDBACK_PATH, {
        "query_id": query_id,
        "timestamp": time.time(),
        "rating": rating,
    })
