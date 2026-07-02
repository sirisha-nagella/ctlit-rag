import boto3

# boto3 automatically finds the credentials in ~/.aws/credentials -
# we never put keys in this file. That separation is the whole point.
s3 = boto3.client("s3")

BUCKET = "ctlit-rag-data-sn84"

#1. List what's in the trials/ prefix, so we know the exact key to fetch

print("Listing objects under trials/ ...")
response = s3.list_objects_v2(Bucket=BUCKET, Prefix="trials/")

keys = [obj["Key"] for obj in response.get("Contents", [])]
print(f"Found {len(keys)} objects. First few:")
for k in keys[:5]:
    print(" ", k)

if not keys:
    raise SystemExit("No objects found under trials/ - nothing to fetch.")

#2. Fetch ONE file and print the first bit of its contents

first_key = keys[0]
print(f"\nFetching {first_key} ...")
obj = s3.get_object(Bucket=BUCKET, Key=first_key)
body = obj["Body"].read().decode("utf-8")

print("first 300 characters of the file:\n")
print(body[:300])

