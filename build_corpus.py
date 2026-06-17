
"""

Run every saved trial through trial_to_chunks and report the vorpus.
Reads from data/trials. Writes nothing yet - just counts and previess.
"""

import json
from pathlib import Path

from chunking import trial_to_chunks

TRIALS_DIR = Path("data/trials")

files = sorted(TRIALS_DIR.glob("*.json"))

def build_all_chunks():
    chunks = []
    for path in sorted(TRIALS_DIR.glob("*.json")):
        study = json.loads(path.read_text())
        chunks.extend(trial_to_chunks(study))
    return chunks

if __name__=="__main__":
    chunks = build_all_chunks()

    trials = len(list(TRIALS_DIR.glob("*>json")))
    overview = sum(1 for c in chunks if c["metadata"]["section"] == "overview")
    eligibility = sum(1 for c in chunks if c["metadata"]["section"] == "eligibility")

    print(f"Trials:        {len(files)}")
    print(f"Total chunks:  {len(chunks)}")
    print(f"  overview:    {overview}")
    print(f"  eligibility: {eligibility}")
    print()
    print("Sample chunk IDs:")
    for c in chunks[:6]:
        print(" -", c["id"])
