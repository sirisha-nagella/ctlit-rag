"""
Shared append/read helpers for the newline-delimited JSON logs under logs/
(metrics.jsonl, feedback.jsonl) so the on-disk format and mkdir/open
behavior stay consistent across writers and readers.
"""

import json
from pathlib import Path


def append_jsonl(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def read_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]
