"""
Compares the two Bedrock A/B arms (nova_micro vs haiku) using
logs/metrics.jsonl (one line per query) and logs/feedback.jsonl 
(one line per thumbs up/down, linked by query_id).

Run from project root: python3 -m scripts.analyze_ab
"""

import statistics
from pathlib import Path

from rag.jsonl import read_jsonl

METRICS_PATH = Path("logs/metrics.jsonl")
FEEDBACK_PATH = Path("logs/feedback.jsonl")


def analyze():
    metrics = read_jsonl(METRICS_PATH)
    feedback = read_jsonl(FEEDBACK_PATH)

    if not metrics:
        print(f"No data in {METRICS_PATH} yet. Run some queries with LLM_BACKEND=bedrock first.")
        return
    
    # most recent rating per query_id (in case of double-clicks)
    ratings_by_query = {}
    for entry in feedback:
        ratings_by_query[entry["query_id"]] = entry["rating"]

    # group metrics rows by which model answered them
    by_model = {}
    for row in metrics:
        by_model.setdefault(row["model_key"], []).append(row)

    print(
        f"{'model':<12} {'n':>4} {'avg latency (s)':>16} {'avg in tok':>11} "
        f"{'avg out tok':>12} {'up':>4} {'down':>6} {'no vote':>8}"
    )
    for model_key, rows in sorted(by_model.items()):
        n = len(rows)
        avg_latency = statistics.mean(r["latency_s"] for r in rows)
        avg_in = statistics.mean(r["input_tokens"] for r in rows)
        avg_out = statistics.mean(r["output_tokens"] for r in rows)

        up = down = no_vote = 0
        for r in rows:
            rating = ratings_by_query.get(r["query_id"])
            if rating == "up":
                up += 1
            elif rating == "down":
                down += 1
            else:
                no_vote += 1

        print(
            f"{model_key:<12} {n:>4} {avg_latency:>16.3f} {avg_in:>11.1f} "
            f"{avg_out:>12.1f} {up:>4} {down:>6} {no_vote:>8}"
        )


if __name__ == "__main__":
    analyze()

