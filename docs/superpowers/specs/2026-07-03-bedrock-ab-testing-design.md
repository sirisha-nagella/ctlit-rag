# Bedrock Migration + A/B Testing — Design Spec

**Date:** 2026-07-03
**Target version:** v0.7.0 (same project, not a new repo)
**Owner:** Sirisha

> **Note (added post-merge):** this is the original design spec, written before
> implementation. A few things changed between this plan and what actually shipped in
> PR #1 — see **Implementation Notes** at the bottom for the honest diff. Kept as-written
> above that section because the plan-vs-actual gap is itself useful interview material.

## Purpose

Replace the local Ollama (`llama3.2:3b`) generation step with Amazon Bedrock, and add a
genuine A/B testing harness comparing two Bedrock models. Two goals driving this:

1. Many target JDs ask for Amazon Bedrock experience; the project currently only
   demonstrates local/self-hosted LLM inference (Ollama) plus AWS deployment
   infrastructure (ECS Fargate) — not managed LLM hosting itself.
2. "A/B testing experience" shows up repeatedly in JDs. This should be a real
   random-assignment experiment with a logged, analyzable result — not a cosmetic
   side-by-side UI demo.

This extends the existing `ctlit-rag` project rather than starting a new one: `boto3` is
already a dependency, the project already has a real AWS deployment story (ECS Fargate),
and the Ollama call is isolated to a single file (`rag/generator.py`), making this a
contained change. The resulting narrative — local-first for free dev, migrated to managed
hosting, then added a cost/quality experiment — is a stronger interview story than a
same-purpose new project would be.

## Decisions

- **Models compared:** Claude 3.5 Haiku vs. Amazon Nova Lite, both via Bedrock.
  Chosen over (a) staying within the Llama family for continuity with the local model —
  weaker A/B story, just comparing sizes of one family — and (b) including a
  Sonnet-tier model — unnecessary cost for an extractive, low-creativity grounded-QA task.
- **A/B mechanism:** random 50/50 assignment per query, with metrics logged for later
  offline analysis. Rejected alternatives: side-by-side compare (2x inference cost per
  query, no statistical rigor, reads as a demo not a test) and confidence-based routing
  (a fallback/routing strategy, not an A/B test — wrong fit for what JDs mean by the term).
- **Quality signal:** explicit user 👍/👎 feedback. This is the lowest-cost signal (no
  extra model call) and the most standard real-world A/B signal (actual user engagement,
  not a model grading itself). An LLM-as-judge score was considered and rejected: it's a
  legitimate technique but a weaker, self-referential signal, and adds a third paid model
  call per query.
- **On Bedrock errors:** no automatic fallback to the other model. Falling back would
  contaminate the random assignment (a query logged as "Nova Lite" could actually have
  been answered by Haiku), breaking the statistical cleanliness the whole A/B story
  depends on. Simpler and more correct to just show a friendly error for that query.

## Non-goals

- No live dashboard or admin page (SQLite + charts). Adds infra/dependencies that serve
  demo flashiness, not the experimentation methodology this is meant to showcase.
- No automatic LLM-as-judge quality scoring.
- No cross-model fallback/retry on error.
- No changes to retrieval, chunking, or the confidence-gating logic in `scripts/ask.py` —
  only the generation step and what wraps it.

## Architecture

```
rag/
  llm/
    bedrock_client.py   # invoke(model_id, system, messages) via Bedrock Converse API
    router.py           # random.choice between Haiku / Nova Lite model IDs
  generator.py           # orchestrates router + bedrock_client; returns answer + metadata
  metrics.py              # append-only JSONL: query_id, model_key, latency_ms, tokens, timestamp, status
  feedback.py             # append-only JSONL: query_id, vote
scripts/
  ask.py                  # unchanged retrieval/confidence logic; now threads query_id/model_key through
  analyze_ab.py            # reads both JSONL logs, joins on query_id, prints a per-model summary table
app.py                    # adds 👍/👎 buttons under each answer, disabled after one click per query
logs/
  ab_events.jsonl
  ab_feedback.jsonl
requirements.txt          # drop `ollama`; `boto3` already present
```

`bedrock_client.py` is a single function rather than one wrapper per model because
Bedrock's Converse API normalizes the request/response shape across model providers —
Claude and Nova Lite are called identically, differing only by `model_id`.

Unchanged: `rag/vector_store.py`, `rag/embedding_model.py`, `chunking.py`,
`scripts/search.py`, and the `DISTANCE_THRESHOLD` confidence gate in `scripts/ask.py`.

## Data Flow

1. User submits a question in `app.py` → `ask(query)`.
2. Existing retrieval + confidence gate runs unchanged (`search.py`, distance threshold).
3. If confident, `ask()` calls `generate_answer(query, chunks)` in `rag/generator.py`.
4. `generator.py` calls `router.pick_model()` → randomly returns
   `("haiku", "anthropic.claude-3-5-haiku-...")` or `("nova-lite", "amazon.nova-lite-v1:0")`.
5. `generator.py` generates a `query_id` (`uuid.uuid4()`), starts a timer, and calls
   `bedrock_client.invoke(model_id, system, messages)`.
6. On success: `bedrock_client.invoke` returns `(answer_text, input_tokens, output_tokens)`;
   `generator.py` stops the timer and calls
   `metrics.log_query(query_id, model_key, latency_ms, input_tokens, output_tokens, status="ok")`,
   appending one line to `logs/ab_events.jsonl`.
7. `generator.py` returns `(answer, model_key, query_id)` up through `ask()` to `app.py`.
8. `app.py` renders the answer and 👍/👎 buttons tagged with `query_id`. On click,
   `feedback.log_feedback(query_id, vote)` appends a line to `logs/ab_feedback.jsonl`, and
   both buttons are disabled for that query in session state. Feedback is optional — a
   query with no click just has no feedback row.
9. Offline, whenever you want a result: `scripts/analyze_ab.py` loads both JSONL files,
   joins on `query_id`, and prints, per model: query count, thumbs-up rate, avg latency,
   estimated cost (hardcoded $/1K-token constants per model, flagged in-code to verify
   against current Bedrock pricing before quoting externally).

## Error Handling

1. **Bedrock throttling (transient):** `bedrock_client.invoke` retries once after a short
   backoff. Other error types (bad credentials, validation, access denied) are not
   retried.
2. **Bedrock call fails after retry:** `generator.py` catches the exception, logs an event
   to `ab_events.jsonl` with `status: "error"` and the `model_key` (so error rate per
   model is itself visible in the analysis), and returns a friendly fallback message to
   the UI in the same style as the existing `NO_MATCH` constant in `scripts/ask.py`. The
   app never crashes on a model error.
3. **Missing/misconfigured AWS credentials or region:** fails fast at app startup (first
   Bedrock client creation, under the existing `@st.cache_resource` pipeline load in
   `app.py`), not silently per query.
4. **Logging write failure** (disk/permissions): `metrics.log_query` and
   `feedback.log_feedback` wrap their file writes in try/except and only warn to stderr —
   a missed log line must never break the user-facing answer.
5. **Duplicate feedback clicks:** once a vote is cast, both buttons are disabled for that
   query in Streamlit session state. Not race-proof, but this is a single-user demo app,
   not a concurrent production system.

## Testing

Follows the existing hermetic pytest convention in `tests/` (no network, no real AWS
calls):

- `router.py`: mock/seed `random.choice`; verify both model keys are reachable and the
  split is roughly even over many calls.
- `bedrock_client.py`: mock the boto3 `bedrock-runtime` client; verify the payload sent to
  `converse()` has the right shape (model_id, messages, system prompt) and that the
  response is parsed into `(text, input_tokens, output_tokens)` correctly.
- `metrics.py` / `feedback.py`: write to a temp file (`tmp_path` fixture); assert the
  JSONL lines are well-formed and appendable.
- `generator.py`: mock `bedrock_client.invoke` to raise; assert it logs a `status: "error"`
  event and returns the friendly fallback message rather than raising.
- `scripts/analyze_ab.py`: given a small fixture pair of `ab_events.jsonl` /
  `ab_feedback.jsonl`, assert the summary table computes the right counts/rates/costs —
  this doubles as documentation of the log schema.

---

## Implementation Notes (added after PR #1 merged — the honest plan-vs-actual diff)

Several things changed between this plan and what actually shipped. None of these are
hidden — naming them is more useful in an interview than pretending the plan was followed
exactly.

- **Models: Claude 3.5 Haiku / Nova Lite (planned) → Claude Haiku 4.5 / Nova Micro
  (shipped).** Newer/cheaper model versions were available by the time of implementation;
  swapped in without re-litigating the "why compare two models, not three" reasoning above,
  which still holds.
- **Ollama was kept as the default backend, not replaced.** The plan said "replace Ollama
  with Bedrock." What shipped is an `LLM_BACKEND` env var: Ollama stays the zero-cost
  default, Bedrock is opt-in. Better outcome than the plan — keeps the free local-dev story
  intact *and* adds the hosted/A/B story, rather than trading one for the other.
- **`requirements.txt` still includes `ollama`** — a direct consequence of the above; the
  plan's "drop `ollama`" line no longer applies.
- **Log filenames: `ab_events.jsonl` / `ab_feedback.jsonl` (planned) → `metrics.jsonl` /
  `feedback.jsonl` (shipped).** Cosmetic naming difference only, same structure and intent.
- **No cost estimation in `analyze_ab.py`.** The plan called for hardcoded $/1K-token
  constants per model; what shipped reports count, avg latency, avg input/output tokens,
  and up/down/no-vote counts, but doesn't convert tokens to a dollar estimate. A real gap
  if cost is the headline question — the raw token counts are there, the $ conversion
  isn't.
- **Credential handling is the opposite of the plan.** The plan said "fail fast at app
  startup" if AWS credentials are missing. A post-merge code-review pass changed this
  deliberately: the boto3 client is now built lazily, on first actual Bedrock call, so that
  running with `LLM_BACKEND=ollama` never requires AWS config at all. Fail-fast was the
  wrong default once Ollama became the primary path again (see above) — failing fast on a
  code path you're not even using would be a worse experience, not a safer one.
- **Retry scope is broader than planned.** The plan only called out throttling as
  retryable. What shipped also retries once on `BotoCoreError` (client-side read/connect
  timeouts), found necessary during real testing, not just throttling `ClientError`s.
- **The plan's biggest miss: Ollama had no metrics/feedback parity at first merge.** The
  initial implementation only logged metrics and captured feedback on the Bedrock path,
  leaving Ollama outside the A/B/analysis story entirely — the plan doesn't explicitly say
  Ollama needs parity, but its absence meant `analyze_ab.py` couldn't compare "local vs.
  hosted," only "hosted model A vs. hosted model B," a narrower result than the project's
  own pitch implies. Fixed in the post-merge code-review pass: `generate_answer` now
  returns the same `(answer, model_key, query_id)` shape for both backends, so Ollama shows
  up in `analyze_ab.py` and gets feedback buttons too.
- **A real, separate bug this same review pass caught: the A/B split was silently broken
  by caching.** `app.py` originally wrapped `run_query` in `st.cache_data`, keyed on the
  question text. `st.cache_data`'s cache is process-wide — so the random model pick and
  metrics logging only ever fired once *per distinct question, for the life of the whole
  app*, not once per ask. Every repeat of a question (a different user, a different
  session, even the same person re-asking) silently reused the cached first answer and
  model instead of running a fresh A/B trial. Fixed by switching to Streamlit
  session-state-scoped memoization instead, so re-runs *within a session* (opening a
  source expander, clicking a feedback button) still skip re-querying, but every genuinely
  new ask gets its own random assignment. This is arguably the most important fix in the
  whole pass: the core mechanism the entire feature exists for was quietly not working as
  designed.
- **Testing section was not followed.** No tests were written for `router.py`,
  `bedrock_client.py`, the Bedrock path in `generator.py`, or `jsonl.py` — `tests/` still
  only covers chunking. Worth being upfront about this rather than implying the planned
  test coverage exists.
