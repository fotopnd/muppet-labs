# Local Harness — Project Plan

_Updated: 2026-06-24 (session 2)_

---

## Session 2 Status (2026-06-24)

**Phase 0 (proxy):** Complete. `lh up` runs, logs to JSONL, `lh logs` displays.

**Phase 1 (characterisation):** Complete. 160 calls across 4 models.

Key findings:
- qwen2.5:7b base: 98% ok
- llama3.1:8b: 88% ok
- mistral:7b: 65% ok (32% refusal)
- qwen2.5-coder:7b: 0% ok, 95% wrap — code fine-tuning regressed tool call schema compliance

**Phase 2 (wrap repair): ABANDONED.** The wrap fix patches qwen2.5-coder but qwen2.5 base already beats it. Low leverage.

**Pivot:** The real question is why tools like Aider fail with local models even when single-turn compliance is decent. Hypothesis: context pressure (long system prompts + file context + multi-turn) degrades compliance on smaller models. Phase 1 tested best-case (20-token prompts, no system prompt). Real usage is 2k–4k token prefix + multi-turn.

**Phase 1.5 (context pressure study):** Built, ready to run.
- `eval/pressure_corpus.py` — generates 45 tasks: 10 base tasks × 4 conditions (bare/sysprompt/context_sm/context_lg) + 5 two-turn chains
- `eval/run_pressure.py` — runner with system prompt injection, context padding, multi-turn with injected fake tool results
- `eval/report_pressure.py` — compliance table by condition + delta bare→context_lg per model
- 4 models × 45 tasks = 180 calls, ~15 min run time
- **Next step: run `python eval/pressure_corpus.py` then `python eval/run_pressure.py`**

Context sizes:
- bare: existing baseline (no system prompt, no context)
- sysprompt: ~500-token Aider-style system prompt
- context_sm: sysprompt + ~1.5k tokens fake file content
- context_lg: sysprompt + ~3k tokens fake file content

Report will show compliance cliff per model. That cliff is the thing to fix in Phase 2.

---

## North Star

A user competent enough to install an IDE can go from "I want to run a local LLM" to "a local
LLM is doing coding work locally." The harness is the reliability layer that makes tool-calling
work against open-weight models — not a pass-through proxy, not a framework.

---

## Thesis

Local models (gemma, qwen-coder, codestral) can technically do agentic coding work. They fail
in practice because tool-call output is unreliable — wrong schema, truncated JSON, prose-wrapped
function calls. Interfaces (Aider, Cursor local mode) fail silently or retry expensively.

A proxy that intercepts, classifies, and repairs these failures in-stream could close the gap
between "model is running" and "model is actually useful." But we don't build repair logic until
we've measured what actually breaks and at what rate.

---

## Structure

Three phases. Phase 0 is a research instrument. Phase 1 is a characterisation study.
Phase 2 is targeted repair informed by that study. Phase 3 is product — only if Phase 2 shows
meaningful improvement.

---

## Phase 0 — Logging Proxy (1–2 days, Rust)

**Goal:** capture raw model outputs before any parsing. This is the instrument for Phase 1.
No repair logic. No clever routing. A thin pipe with a JSONL log.

### What it does

- Receives OpenAI-compatible `POST /v1/chat/completions` requests
- Forwards to Ollama at the configured upstream URL
- Captures the raw response body (streamed or complete) before returning it
- Writes one JSONL entry per request:

```json
{
  "ts": "2026-06-24T14:00:00Z",
  "model": "qwen2.5-coder:7b",
  "tool_schemas": [...],
  "messages": [...],
  "raw_response": "...",
  "stream": true,
  "parse_ok": false,
  "latency_ms": 1240
}
```

### CLI

```
lh up [--port 8080] [--target http://localhost:11434] [--log ~/.local/share/lh/requests.jsonl]
lh logs [--tail 20] [--failures-only]
```

### Rust file structure

```
src/
├── main.rs        ← tokio entry, wires CLI → runtime
├── cli.rs         ← clap: lh up, lh logs
├── config.rs      ← harness.toml + env overrides + defaults
├── proxy.rs       ← axum POST /v1/chat/completions handler
├── upstream.rs    ← reqwest client, streaming passthrough, raw capture
└── logger.rs      ← async JSONL writer
```

### Cargo.toml (corrected)

```toml
[dependencies]
tokio        = { version = "1", features = ["full"] }
axum         = "0.7"
tower        = { version = "0.4", features = ["util", "timeout"] }
reqwest      = { version = "0.12", features = ["stream", "json"] }
serde        = { version = "1", features = ["derive"] }
serde_json   = "1"
clap         = { version = "4", features = ["derive", "env"] }
futures-util = "0.3"
toml         = "0.8"
tracing      = "0.1"
tracing-subscriber = { version = "0.3", features = ["json"] }
```

### Verification

Route a coding task through the proxy to Ollama. Confirm `requests.jsonl` captures the raw
response including any malformed output. `lh logs --failures-only` shows parse failures.

---

## Phase 1 — Characterisation Study (3–5 days, Python eval harness)

**Goal:** measure tool-call failure rate by pattern, model, and task complexity. Produce a
frequency table that drives Phase 2 prioritisation.

### Eval corpus

A bespoke set of ~100 tasks, not full BFCL (overkill for local models). Four task categories
matching the complexity gradient where failures appear:

| Category | Description | Example |
|---|---|---|
| Single | One tool call, simple params | `read_file("main.py")` |
| Sequential | Two calls in order | read file, then write modified version |
| Conditional | Call depends on prior result | search → if found, read → edit |
| Parallel | Two independent calls | read two files simultaneously |

### Tool schema set

Four tools that cover agentic coding work:

```json
[
  {"name": "read_file",    "parameters": {"path": "string"}},
  {"name": "write_file",   "parameters": {"path": "string", "content": "string"}},
  {"name": "run_command",  "parameters": {"cmd": "string"}},
  {"name": "search_files", "parameters": {"pattern": "string", "directory": "string"}}
]
```

### Failure taxonomy

Tag each output with one primary pattern:

| Tag | Description |
|---|---|
| `ok` | Valid JSON, correct schema, correct function, correct params |
| `wrap` | JSON embedded in prose or markdown code block |
| `truncated` | Valid JSON structure cut off — unclosed brackets |
| `schema_drift` | Valid JSON but wrong field names or missing required fields |
| `type_error` | Correct structure but wrong value types |
| `hallucinated_tool` | Calls a tool not in the schema |
| `refusal` | No tool call at all — prose response |

### Models under test

- `gemma2:9b`
- `qwen2.5-coder:7b`
- `codestral:22b` (if available)

### Eval harness (Python)

```
eval/
├── corpus.json      ← task definitions: schema + prompt + expected_tool + expected_params
├── run_eval.py      ← sends each task through lh proxy, writes raw_outputs.jsonl
├── classify.py      ← reads raw_outputs.jsonl, tags each entry, writes classified.jsonl
└── report.py        ← frequency table: pattern × model × category
```

### Output

A table like:

```
pattern          gemma2  qwen-coder  codestral
wrap               41%        18%        6%
schema_drift       12%        22%       11%
truncated           8%         6%        4%
type_error          4%         8%        2%
hallucinated        6%         3%        1%
refusal            11%         5%        2%
ok                 18%        38%       74%
```

This table is the decision input for Phase 2. If `wrap` is dominant and `refusal` is low, build
the stripping layer. If `schema_drift` dominates, the repair surface is different.

---

## Phase 2 — Targeted Repair (1–2 weeks, Rust)

**Goal:** implement repair for the top fixable patterns, re-run the benchmark, measure delta.

Only start this phase after the Phase 1 table exists.

### Repair priority heuristic

Build for: **high frequency AND fixable in-stream**.

| Pattern | Fixable in proxy? | Approach |
|---|---|---|
| `wrap` | Yes | Strip ` ```json ``` ` wrappers and leading/trailing prose |
| `truncated` | Yes | Greedy bracket-stack completion on stream end |
| `type_error` | Yes | Cast against known schema after parse |
| `schema_drift` | Partial | Fuzzy field-name matching against known schema |
| `hallucinated_tool` | No | Reject + retry with explicit schema reminder |
| `refusal` | No | Model limitation — out of scope |

### Stream repair architecture

The repair layer sits between `upstream.rs` (raw bytes from Ollama) and the response sent to
the client. For streaming responses, buffer the tool-call JSON block, attempt repair on stream
close if parse fails, then flush the repaired output.

```
upstream bytes → stream buffer → [repair layer] → client
                                      ↑
                                 only activates on
                                 parse failure
```

The client sees a small latency increase only on failure (repair is on the error path, not the
happy path).

### Benchmark delta

Re-run the exact Phase 1 corpus after implementing repair. Report:
- Before/after success rate per model
- Per-pattern resolution rate (what fraction of `wrap` failures were fixed)
- Latency overhead on the error path

This delta is the portfolio claim. "Improved qwen-coder single-task success rate from 38% to X%
by implementing stream-aware repair for content-wrapping and truncation."

---

## Phase 3 — Product (only if Phase 2 delta is meaningful)

**Gate:** if Phase 2 improves overall success rate by >15pp for at least one model on single/sequential
tasks, productise. Otherwise, the study and repair layer are the deliverable.

If gated in:
- `lh up` as the single entry point — start proxy, tail logs, show live stats
- `harness.toml` for model routing (e.g. code tasks → qwen-coder, chat → gemma)
- README with "zero to working local LLM in 5 minutes" install path
- Single compiled binary distribution

---

## What this is NOT

- A generic OpenAI-compatible proxy (LiteLLM exists)
- A self-healing "platform" (marketing, not engineering)
- MCP tool server (orthogonal to this problem)
- A replacement for Cursor or Aider (it's a reliability layer under them)

---

## Portfolio story

An empirical characterisation of tool-call reliability in open-weight local models, with a
stream-aware repair layer benchmarked before and after. The study is the contribution — the
repair layer is the artefact. Both are demonstrable, specific, and directly relevant to
evaluation methodology and failure analysis in LLM systems.
