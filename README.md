# Clinical Trial & Literature RAG Assistant (`ctlit-rag`)

A Retrieval-Augmented Generation assistant that answers questions about Gilead
clinical trials and related published research. Every answer is **grounded in
retrieved sources**: the app shows the matching documents and their vector
similarity distances, and it refuses to answer when nothing relevant is
retrieved (confidence gating), so it doesn't hallucinate trials or numbers.

## Architecture

```
ClinicalTrials.gov API ─┐
                        ├─► scripts/fetch_trials.py ─► data/trials/*.json
PubMed E-utilities ─────┘                 │
                                          ▼
                 chunking.py  (trial_to_chunks / paper_to_chunks)
                                          ▼
             rag/embedding_model.py  (all-MiniLM-L6-v2, 384-dim)
                                          ▼
             rag/vector_store.py  (ChromaDB, cosine → chroma_store/)
                                          ▼
   scripts/search.py ─► scripts/ask.py  (confidence gate @ 0.50 + generate)
                                          ▼
                        rag/generator.py  (LLM_BACKEND switch)
                              │                      │
                    LLM_BACKEND=ollama      LLM_BACKEND=bedrock
                              │                      │
                   Ollama llama3.2:3b     rag/llm/router.py (A/B: Nova Micro
                   (temperature 0.2)      vs Claude Haiku 4.5, random pick)
                              │                      │
                              │           rag/llm/bedrock_client.py
                              │           (Converse API, retry on throttle)
                              │                      │
                              └──────────►rag/metrics.py (latency/tokens → logs/metrics.jsonl)
                                                      │
                        app.py  (Streamlit UI, shows model used)
                                                      │
                        rag/feedback.py (thumbs up/down → logs/feedback.jsonl)
                                                      │
                        scripts/analyze_ab.py (compares model arms)
                                          ▼
        Docker → AWS ECS Fargate  (ollama sidecar + app container)
```

## Local setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Build the vector store

`chroma_store/` is **not** committed to git — rebuild it from source:

```bash
./scripts/rebuild_store.sh
```

This fetches the trials + papers, chunks and embeds them, and populates
`chroma_store/`. (You also need a local [Ollama](https://ollama.com) with
`ollama pull llama3.2:3b` running for generation.)

### Run

```bash
# Streamlit directly (needs Ollama running locally):
streamlit run app.py

# ...or the whole thing (app + ollama) with Docker:
docker compose up --build
```

Open http://localhost:8501.

### Bedrock backend + A/B testing (v0.7.0)

By default the app generates with local Ollama. Set `LLM_BACKEND=bedrock` (and
have AWS credentials configured) to switch generation to Amazon Bedrock instead:

```bash
export LLM_BACKEND=bedrock
streamlit run app.py
```

On the Bedrock path, `rag/llm/router.py` randomly assigns each query to one of
two models — Amazon Nova Micro or Claude Haiku 4.5 — so the two arms get
roughly even traffic. Every query, on either backend (Ollama included, tagged
`model_key="ollama"`), logs its model, token counts, and latency to
`logs/metrics.jsonl` via `rag/metrics.py`; the UI shows which model answered
and lets you rate the answer thumbs up/down, logged to `logs/feedback.jsonl`
via `rag/feedback.py` and linked back to the query by `query_id`. Compare
model arms (latency, tokens, feedback) with:

```bash
python3 -m scripts.analyze_ab
```

`rag/llm/bedrock_client.py` retries once on Bedrock throttling
(`ThrottlingException` / `ServiceUnavailableException` / `ModelTimeoutException`)
before raising — hit this for real during testing, not just defensive code.

## Deploy (AWS ECS Fargate)

1. Build and push the image to ECR:
   ```bash
   docker build -t ctlit-rag .
   docker tag ctlit-rag <acct>.dkr.ecr.us-east-1.amazonaws.com/ctlit-rag:latest
   docker push <acct>.dkr.ecr.us-east-1.amazonaws.com/ctlit-rag:latest
   ```
2. Register `task-definition.json` (fill in `<YOUR_AWS_ACCOUNT_ID>`) and run it
   as a Fargate service. The task runs two containers: an `ollama` sidecar
   (which pulls the model on start; the `app` waits until it is `HEALTHY`) and
   the Streamlit `app`.

> **Note:** Fargate has no GPU, so `llama3.2:3b` runs on CPU — the *first*
> question is slow (model cold-load) and later ones are faster once warm.
> The Docker image installs the **CPU-only** torch build to avoid shipping the
> unused ~2 GB CUDA libraries.

## Tests

```bash
python -m pytest tests/        # or: python tests/test_chunking.py
```

The tests are hermetic (no network, no data files).

## Project layout

| Path | Purpose |
|------|---------|
| `app.py` | Streamlit UI (shows model used, thumbs up/down feedback) |
| `chunking.py` | **Canonical** chunker that builds the live store |
| `rag/` | embedding model, Chroma vector store, generator (Ollama + Bedrock) |
| `rag/llm/router.py` | A/B model picker (Nova Micro vs Claude Haiku 4.5) |
| `rag/llm/bedrock_client.py` | Bedrock Converse API client, retries on throttling |
| `rag/metrics.py` | per-query latency/token logging (`logs/metrics.jsonl`) |
| `rag/feedback.py` | thumbs up/down logging (`logs/feedback.jsonl`), linked by `query_id` |
| `rag/jsonl.py` | shared append/read helpers used by `metrics.py`, `feedback.py`, `analyze_ab.py` |
| `scripts/` | fetch / load / search / ask + `rebuild_store.sh` |
| `scripts/analyze_ab.py` | compares latency/tokens/feedback across model arms |
| `data_sources/` | ClinicalTrials.gov and PubMed clients |
| `tests/` | hermetic unit tests |
| `archive/` | superseded scripts, kept for reference (see below) |
| `Dockerfile`, `docker-compose.yml`, `task-definition.json` | deployment |

### About `archive/`

`archive/` holds the earlier FAISS-based build pipeline and a richer, unused
chunker (`archive/chunker.py`) that adds interventions and token-based
sub-chunking. It is **not** wired into the live store — its metadata differs
from what `app.py` expects. Adopting it would be a deliberate migration:
align the metadata, rebuild the store, and re-validate retrieval.
