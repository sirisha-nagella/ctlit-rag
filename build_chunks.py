
import boto3, json
from collections import Counter
from chunker import extract_chunks, sub_chunk


s3 = boto3.client("s3")
BUCKET = "ctlit-rag-data-sn84"

# 1. List every trial under trials/
resp = s3.list_objects_v2(Bucket=BUCKET, Prefix="trials/")
keys = [o["Key"] for o in resp.get("Contents", []) if o["Key"].endswith(".json")]
print(f"Found {len(keys)} trial files.\n")

#2. Fetch, parse, chunk each one
all_chunks = []
section_counts = Counter()
thin_trials = [] # trials that produced suspiciously few chunks


for key in keys:
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    trial = json.loads(obj["Body"].read().decode("utf-8"))
    chunks = extract_chunks(trial, source_key=key)
    chunks = [sc for c in chunks for sc in sub_chunk(c)]
    


    all_chunks.extend(chunks)
    for c in chunks:
        section_counts[c["metadata"]["section"]] += 1
    if len(chunks) < 2:
        thin_trials.append((key, len(chunks)))

#3. Aggregate health report
print(f"Total chunks across all trials: {len(all_chunks)}")
print(f"Avg chunks per trial: {len(all_chunks) / len(keys):.1f}\n")
print("Chunks per section:")
for section, n in section_counts.most_common():
    print(f"   {section:15} {n}")

if thin_trials:
    print("\n! Trials that produced <2 chunks (worth inspecting):")
    for key, n in thin_trials:
        print(f"  {key}: {n} chunks(s)")

else:
    print("\n✅ Every trial produced at least 2 chunks.")

# 4. Cache to disk so dev iterations don't re-hit S3 every run

with open("chunks.json", "w") as f:
    json.dump(all_chunks, f, indent=2)
print(f"\nWrote {len(all_chunks)} chunks to chunks.json")

