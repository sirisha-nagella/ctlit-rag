"""
Eval harness - Phase 1: (retrieval + confidence gating) + Phase 2 (groundedness)
No LLM calls. Run: Python -m evals.run_eval
"""

import json
import re
from pathlib import Path

from scripts.search import search
from scripts.ask import ask, DISTANCE_THRESHOLD

GOLDEN_PATH = Path("evals/fixtures/golden_queries.jsonl")
NCT_RE = re.compile(r"NCT\d{8}")


def load_golden_queries():
    with GOLDEN_PATH.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    queries = load_golden_queries()
    passed = 0

    for q in queries:
        hits = search(q["query"], k=3)
        best_distance = hits[0][2] if hits else None
        confident = best_distance is not None and best_distance <= DISTANCE_THRESHOLD
        distance_str = f"{best_distance:.3f}" if best_distance is not None else "N/A"

        if q["label"] == "should_answer":
            retrieved_refs = [meta.get("nct_id") or meta.get("pmid") for _doc, meta, _dist in hits]
            hit = q["expected_ref"] in retrieved_refs
            ok = hit and confident
            print(f"[{q['id']}] should_answer: hit={hit}, confident={confident}, distance={distance_str}")

            if ok:
                answer, _, _, _, _ = ask(q["query"])
                cited = set(NCT_RE.findall(answer))
                ungrounded = cited - set(retrieved_refs)
                grounded = len(ungrounded) == 0
                ok = ok and grounded
                print(f"   grounded={grounded} (cited={cited}, ungrounded={ungrounded})")
        else:
            ok = not confident
            print(f"[{q['id']}] should_refuse: confident={confident}, distance={distance_str}")

        passed += ok

    print(f"\n{passed}/{len(queries)} passed")

if __name__ == "__main__":
    main()

