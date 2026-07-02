
"""
Step 9 - Generation.

Takes a user question, retrieves the top-k chunks (step-8),
and feeds them to a local Ollama model with strict instructiuons to 
answer ONLY from the provided context and cite
the chunk/trial IDs it used.

Run from project root:
    Python3 generate.py
"""

import json, urllib.request
from retrieve import retrieve

question = "what are the eligibility criteria for HIV trials?"
chunks = retrieve(question, k=5)

context = "\n\n".join(f"[{c['id']}]\n{c['text']}" for c in chunks)
prompt = f"Answer the question using ONLY this context. Cite chunk ids in brackets.\n\nCONTEXT:\n{context}\n\nQUESTION:\n{question}\n\nANSWER:"

payload = json.dumps({"model": "llama3.2:3b", "prompt": prompt, "stream": False}).encode()
req = urllib.request.Request("http://localhost:11434/api/generate", data=payload, headers={"Content-Type": "application/json"})
result = json.loads(urllib.request.urlopen(req).read())

print(result["response"])




