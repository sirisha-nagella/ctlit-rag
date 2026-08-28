"""
Eval harness - Phase 1: (retrieval + confidence gating) + Phase 2 (groundedness)
No LLM calls beyond what ask() already makes to produce an answer to check.

Phase 3 (answer comparison across Ollama / Haiku / Nova Micro) is opt-in, since it
makes real, paid Bedrock calls and needs AWS credentials configured:

    RUN_PHASE3=1 python -m evals.run_eval

Run: python -m evals.run_eval
"""

import os
import json
import re
import time
from pathlib import Path

import ollama

from scripts.search import search
from scripts.ask import ask, DISTANCE_THRESHOLD
from rag.generator import _build_prompt, SYSTEM, MODEL as OLLAMA_MODEL
from rag.llm.router import MODELS as BEDROCK_MODELS
from rag.llm import bedrock_client

GOLDEN_PATH = Path("evals/fixtures/golden_queries.jsonl")
NCT_RE = re.compile(r"NCT\d{8}")
PMID_RE = re.compile(r"PMID\s*:?\s*(\d+)", re.IGNORECASE)


def load_golden_queries():
    with GOLDEN_PATH.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def check_grounded(answer, retrieved_refs):
    """Same rule as Phase 2: any cited NCT/PMID must be one we actually retrieved."""
    cited = set(NCT_RE.findall(answer)) | set(PMID_RE.findall(answer))
    ungrounded = cited - set(retrieved_refs)
    return cited, ungrounded, len(ungrounded) == 0


def _call_ollama(prompt):
    start = time.time()
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        options={"temperature": 0.2},
    )
    latency_s = time.time() - start
    answer = response["message"]["content"].strip()
    return answer, response.get("prompt_eval_count", 0), response.get("eval_count", 0), latency_s


def _call_bedrock(model_id, prompt):
    start = time.time()
    answer, input_tokens, output_tokens = bedrock_client.invoke(
        model_id, SYSTEM, [{"role": "user", "content": prompt}]
    )
    return answer, input_tokens, output_tokens, time.time() - start


# Each entry bypasses rag/generator.py's LLM_BACKEND/router logic on purpose - this
# always tests all three backends directly, regardless of what LLM_BACKEND is set to.
PHASE3_BACKENDS = [
    ("ollama", lambda prompt: _call_ollama(prompt)),
    ("haiku", lambda prompt: _call_bedrock(BEDROCK_MODELS["haiku"], prompt)),
    ("nova_micro", lambda prompt: _call_bedrock(BEDROCK_MODELS["nova_micro"], prompt)),
]


def run_phase3(cases):
    """cases: list of (query_id, prompt, retrieved_refs) for queries that passed
    Phase 1 (hit + confident). Opt-in - see module docstring."""
    print("\n--- Phase 3: backend comparison (Ollama / Haiku / Nova Micro) ---")

    stats = {name: {"n": 0, "grounded": 0, "skipped": 0, "latencies": [], "in_toks": [], "out_toks": []}
              for name, _ in PHASE3_BACKENDS}

    for query_id, prompt, retrieved_refs in cases:
        for name, call in PHASE3_BACKENDS:
            try:
                answer, in_tok, out_tok, latency = call(prompt)
            except Exception as e:
                print(f"  [{query_id}] {name}: skipped ({type(e).__name__}: {e})")
                stats[name]["skipped"] += 1
                continue

            _, ungrounded, grounded = check_grounded(answer, retrieved_refs)
            s = stats[name]
            s["n"] += 1
            s["grounded"] += int(grounded)
            s["latencies"].append(latency)
            s["in_toks"].append(in_tok)
            s["out_toks"].append(out_tok)
            print(f"  [{query_id}] {name}: grounded={grounded} latency={latency:.2f}s in_tok={in_tok} out_tok={out_tok}")

    print(f"\n{'backend':<12} {'n':>4} {'grounded':>9} {'avg latency(s)':>15} {'avg in tok':>11} {'avg out tok':>12} {'skipped':>8}")
    for name, s in stats.items():
        if s["n"] == 0:
            print(f"{name:<12} {0:>4} {'-':>9} {'-':>15} {'-':>11} {'-':>12} {s['skipped']:>8}")
            continue
        avg_latency = sum(s["latencies"]) / s["n"]
        avg_in = sum(s["in_toks"]) / s["n"]
        avg_out = sum(s["out_toks"]) / s["n"]
        print(f"{name:<12} {s['n']:>4} {s['grounded']:>9} {avg_latency:>15.2f} {avg_in:>11.1f} {avg_out:>12.1f} {s['skipped']:>8}")


def main():
    queries = load_golden_queries()
    passed = 0
    phase3_cases = []

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
                cited, ungrounded, grounded = check_grounded(answer, retrieved_refs)
                ok = ok and grounded
                print(f"   grounded={grounded} (cited={cited}, ungrounded={ungrounded})")

                chunks = [doc for doc, meta, dist in hits]
                prompt = _build_prompt(q["query"], chunks)
                phase3_cases.append((q["id"], prompt, retrieved_refs))
        else:
            ok = not confident
            print(f"[{q['id']}] should_refuse: confident={confident}, distance={distance_str}")

        passed += ok

    print(f"\n{passed}/{len(queries)} passed")

    if os.getenv("RUN_PHASE3"):
        run_phase3(phase3_cases)
    else:
        print("\n(Phase 3 backend comparison skipped - set RUN_PHASE3=1 to run it; makes real Bedrock calls)")

if __name__ == "__main__":
    main()
