
import boto3, json
from chunker import extract_chunks

s3 = boto3.client("s3")
BUCKET = "ctlit-rag-data-sn84"

resp = s3.list_objects_v2(Bucket=BUCKET, Prefix="trials/")
first_key = resp["Contents"][0]["Key"]
obj = s3.get_object(Bucket=BUCKET, Key=first_key)
trial = json.loads(obj["Body"].read().decode("utf-8"))

chunks = extract_chunks(trial, source_key=first_key)

print(f"{first_key} produced {len(chunks)} chunks:\n")
for c in chunks:
    print("=" * 70)
    print("ID:     ", c["id"])
    print("META:   ", {k: c["metadata"][k] for k in ("nct_id", "conditions", "phases")})
    print("TEXT:")
    print(c["text"][:400] + (" ..." if len(c["text"]) > 400 else ""))
    print()


