import json, statistics
from sentence_transformers import SentenceTransformer

# all-MiniLM-L6-v2 is the classical local default: small, fast, 384-dim.
# We use its tokenizer to measure - its limit is representative of the family.

MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)
limit = model.max_seq_length    # the model's hard token ceiling
tok = model.tokenizer

with open("chunks.json") as f:
    chunks = json.load(f)

rows = [(len(tok.encode(c["text"])), c["metadata"]["section"], c["id"]) for c in chunks]
rows.sort(reverse=True)
counts = [r[0] for r in rows]

print(f"Model: {MODEL_NAME}  |  max_seq_length (token_limit): {limit}\n")
print(f"Chunks: {len(chunks)}")
print(f"Tokens - min {min(counts)}, median {int(statistics.median(counts))}, "
      f"mean {int(statistics.mean(counts))}, max {max(counts)}\n")


over = [r for r in rows if r[0] > limit]
print(f"Chunks exceeding the {limit}-token limit: {len(over)} "
      f"({len(over)/len(chunks)*100:.0f}%)")


# which sections are the offenders?
from collections import Counter
sec_over = Counter(r[1] for r in over)
if sec_over:
    print("Overflow by section:", dict(sec_over))
    print("\nLongest 10 chunks:")
    for n, sec, cid in rows[:10]:
        flag = " ! OVER" if n > limit else ""
        print(f" {n:5} tokens [{sec:13}] {cid}{flag}")

