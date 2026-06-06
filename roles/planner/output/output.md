# Planner Output — system-prompt-injection-detector

**Role:** planner
**Sequence:** `new-project-full` (step 2)
**Date:** 2026-06-06

---

## Project

`system-prompt-injection-detector` — a DistilBERT binary classifier trained on the SPML prompt injection benchmark (augmented with Ollama-generated synthetic benign examples), wrapped in a FastAPI service that scores each field of an agent request independently, logs all detections to Postgres, and exposes a proxy endpoint that blocks flagged requests before they reach a downstream LLM.

---

## Brief Flags Resolved

**Flag: proxy endpoint v1 or v2**
Decision: v1. The proxy endpoint (`POST /proxy`) is a single handler (~30 lines) that reads `DOWNSTREAM_LLM_URL` from env, calls `/detect` internally, and either forwards or rejects. Including it in v1 is the correct call — it is the signal that distinguishes a toy classifier from a production middleware pattern.

**Flag: separate React SPA vs FastAPI-served dashboard**
Decision: separate React SPA. Same pattern as other workspace projects. FastAPI serves JSON only; the React app is built with Vite and runs on a separate dev port (5173). Production deployment would use a static file host or a separate container, but that is out of scope for v1.

**Flag: synthetic negatives generation — CLI script**
Decision: CLI script `uv run generate-negatives --count 5000` in the training project. It calls Ollama at `http://localhost:11434`, uses qwen2.5-coder:7b, writes output to `data/negatives.jsonl`. This runs before training and is a documented manual prerequisite. The training script reads the JSONL file; it does not call Ollama itself.

**Flag: SPML dataset field names**
Decision: open question escalated to architect. Implementer must run `from datasets import load_dataset; ds = load_dataset("reshabhs/SPML_Chatbot_Prompt_Injection"); print(ds["train"].features)` before writing the data loader. Architect documents the likely field names and the inspection step.

**Flag: tool_outputs field naming in detection_log**
Decision: `field_results` column is JSONB — it stores the full list of `FieldResult` objects as JSON. Variable-length tool_outputs list is naturally accommodated; no schema migration needed when tool_outputs grows or shrinks.

---

## Requirements

### Training Project (`injection-detector-training/`)

1. `uv run generate-negatives --count N` calls Ollama (qwen2.5-coder:7b) N times with the standard benign prompt template, collects responses, and writes `data/negatives.jsonl` where each line is `{"text": "...", "label": 0}`. Exits with an error if Ollama is not reachable.
2. `uv run train` loads the SPML dataset from HuggingFace, loads `data/negatives.jsonl`, concatenates them into a combined dataset, applies an 80/10/10 train/val/test split with seed=42, tokenises with `distilbert-base-uncased` tokeniser, and fine-tunes via HuggingFace `Trainer` for 4 epochs with batch_size=64 on MPS.
3. Training uses `warmup_steps` (integer, not `warmup_ratio`), `eval_strategy="epoch"`, `save_strategy="epoch"`, `load_best_model_at_end=True`, metric_for_best_model="eval_f1". No `no_cuda` flag; Trainer auto-detects MPS.
4. `uv run evaluate` loads the best checkpoint, runs inference on the test split, computes F1, precision, recall, AUC-ROC, and calibration bins (10 equal-width bins from 0.0 to 1.0), and writes results to `resources/evals/injection-detector-training/distilbert-base-uncased-<timestamp>.json`.
5. Checkpoint is saved to `resources/models/injection-detector-training/distilbert-base-uncased-<YYYY-MM-DD>/` via `model.save_pretrained()` + `tokenizer.save_pretrained()`.
6. All training utilities are unit-tested: dataset loading (mock HF call), negatives loading, combined dataset construction, label alignment (injection=1, benign=0). Model forward pass tested with mock weights.

### Detection Service (`injection-detector/`)

7. `POST /detect` accepts `DetectionRequest` body: `{system_prompt: str, user_message: str, tool_outputs: list[str]}`. Loads classifier once at startup (from `MODEL_CHECKPOINT_DIR` env var). Scores `system_prompt`, `user_message`, and each element of `tool_outputs` independently. Returns `DetectionResponse` with per-field results, `overall_flagged` (True if any field exceeds threshold), and `max_probability`. Threshold read from `INJECTION_THRESHOLD` env var (default 0.7).
8. `POST /proxy` reads `DetectionRequest` body. Calls the detection logic internally. If `overall_flagged=True`, returns HTTP 400 with `DetectionResponse` as JSON body. If not flagged, forwards the original request body to `DOWNSTREAM_LLM_URL` via httpx and returns the upstream response unchanged (status code and body).
9. Every `/detect` call (and every `/proxy` call that triggers detection) is logged to the `detection_log` Postgres table synchronously before the response is returned.
10. `GET /logs` returns a paginated list of `DetectionLog` records (page, page_size query params; default page_size=50). Supports optional `flagged_only: bool` filter.
11. `GET /logs/stats` returns aggregate statistics: total detections, total flagged, flag rate by field name, daily counts for last 30 days.
12. `GET /eval` reads the latest eval JSON from `resources/evals/injection-detector-training/` (sorted by filename timestamp) and returns it as JSON.
13. The classifier is loaded once at startup via a lifespan context manager. Attempting to call `/detect` before the model is loaded raises HTTP 503, not a silent wrong result.
14. All API endpoints have pytest integration tests with a test database (separate `TEST_DATABASE_URL` env var) and a mock classifier that returns fixed probabilities.
15. Postgres connection string read from `DATABASE_URL` env var. Port 5438 by default (documented in `.env.example`).

### Dashboard (`injection-detector-dashboard/`)

16. Tab 1 — Detection Log: paginated table of `DetectionLog` records. Columns: timestamp, overall_flagged badge (green/red), max_probability, field breakdown (expandable row). `flagged_only` toggle filter (dropdown: All / Flagged Only). Fetches from `GET /logs`.
17. Tab 2 — Field Analysis: bar chart showing flag rate (%) for each field: system_prompt, user_message, tool_output_0 … tool_output_N. Uses recharts `BarChart`. Data from `GET /logs/stats`.
18. Tab 3 — Confidence Distribution: histogram with 10 equal-width bins (0.0–0.1, 0.1–0.2, …, 0.9–1.0). Two data series per bin: flagged count and benign count. Rendered as grouped `BarChart` in recharts. Data computed client-side from a full probability dump endpoint or from `/logs/stats` (architect decides).
19. Tab 4 — Model Card: displays F1, precision, recall, AUC-ROC from the latest eval JSON. Calibration chart: bar chart of 10 bins showing mean predicted probability vs fraction of positives (same bin schema as confidence distribution). Data from `GET /eval`.
20. All TanStack Query hooks have loading and error states handled. No bare `useEffect` + `fetch`.
21. Dashboard vitest tests cover: DetectionLogTable renders rows, FieldAnalysisChart renders with mock data, ConfidenceHistogram renders bins correctly, ModelCard renders metrics.

---

## Technology Stack

### Training Project

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | workspace standard |
| Package manager | uv | workspace standard |
| Formatter/linter | ruff | workspace standard |
| ML framework | HuggingFace transformers + datasets | established pattern; Trainer handles MPS |
| Acceleration | accelerate | explicit dep required by Trainer ≥5.x |
| Base model | distilbert-base-uncased | small, fast, proven binary classifier |
| Synthetic data | Ollama (qwen2.5-coder:7b) via httpx | Ollama running locally; no API cost |
| Eval metrics | scikit-learn | F1, precision, recall, AUC-ROC |
| Testing | pytest | workspace standard |
| Device | MPS (Apple M4 24GB) | constraint from brief |

### Detection Service

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | workspace standard |
| Package manager | uv | workspace standard |
| Formatter/linter | ruff | workspace standard |
| Web framework | FastAPI | async, typed, Pydantic v2 native |
| ORM | SQLAlchemy 2.x (async) | async sessions; Pydantic-compatible |
| DB driver | asyncpg | async Postgres |
| HTTP client | httpx | async; used for proxy forwarding |
| DB | Postgres (port 5438) | constraint from brief |
| Settings | pydantic-settings with extra="ignore" | workspace convention |
| Testing | pytest + pytest-asyncio | async endpoint tests |
| DB (test) | separate TEST_DATABASE_URL | no shared state with dev DB |

### Dashboard

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | TypeScript 5.x, strict mode | workspace standard |
| Framework | React 18 | workspace standard |
| Package manager | pnpm | workspace standard |
| Formatter/linter | prettier + eslint (flat config) | workspace standard |
| Build tool | Vite | workspace standard |
| Server state | TanStack Query | workspace standard |
| Charts | recharts | specified in brief |
| UI components | shadcn/ui | workspace standard |
| Testing | vitest + @testing-library/react | workspace standard |

---

## File and Module Structure

```
projects/system-prompt-injection-detector/
│
├── injection-detector-training/          ← standalone uv project
│   ├── pyproject.toml
│   ├── .env.example
│   ├── data/
│   │   ├── negatives.jsonl               ← generated by generate-negatives CLI (gitignored)
│   │   └── .gitkeep
│   ├── src/
│   │   └── injection_detector_training/
│   │       ├── __init__.py
│   │       ├── config.py                 ← pydantic-settings Settings class
│   │       ├── dataset.py                ← load_spml, load_negatives, build_dataset
│   │       ├── generate_negatives.py     ← CLI entry point: calls Ollama, writes JSONL
│   │       ├── train.py                  ← CLI entry point: Trainer setup + run
│   │       ├── evaluate.py               ← CLI entry point: load checkpoint, compute metrics
│   │       └── metrics.py                ← compute_metrics callback + calibration bins
│   └── tests/
│       ├── conftest.py
│       ├── test_dataset.py
│       ├── test_generate_negatives.py
│       └── test_evaluate.py
│
├── injection-detector/                   ← FastAPI service
│   ├── pyproject.toml
│   ├── .env.example
│   ├── src/
│   │   └── injection_detector/
│   │       ├── __init__.py
│   │       ├── config.py                 ← pydantic-settings Settings
│   │       ├── models.py                 ← Pydantic: DetectionRequest, FieldResult, DetectionResponse
│   │       ├── db/
│   │       │   ├── __init__.py
│   │       │   ├── engine.py             ← async engine + session factory
│   │       │   └── orm.py                ← DetectionLog SQLAlchemy ORM model
│   │       ├── classifier.py             ← Classifier wrapper: load, predict_field, predict_all
│   │       ├── detection.py              ← run_detection() business logic (no HTTP)
│   │       ├── routers/
│   │       │   ├── __init__.py
│   │       │   ├── detect.py             ← POST /detect, POST /proxy
│   │       │   └── logs.py               ← GET /logs, GET /logs/stats, GET /eval
│   │       └── main.py                   ← FastAPI app + lifespan (model load)
│   └── tests/
│       ├── conftest.py                   ← test DB, mock classifier fixture
│       ├── test_detect.py
│       ├── test_proxy.py
│       └── test_logs.py
│
└── injection-detector-dashboard/         ← React SPA
    ├── package.json
    ├── pnpm-lock.yaml
    ├── vite.config.ts
    ├── tsconfig.json
    ├── .env.example
    ├── eslint.config.ts
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx                       ← tab layout (shadcn Tabs)
    │   ├── api/
    │   │   └── client.ts                 ← base fetch wrapper
    │   ├── hooks/
    │   │   ├── useLogs.ts                ← GET /logs TanStack Query hook
    │   │   ├── useLogStats.ts            ← GET /logs/stats hook
    │   │   └── useEval.ts                ← GET /eval hook
    │   ├── components/
    │   │   ├── DetectionLogTable.tsx
    │   │   ├── FieldAnalysisChart.tsx
    │   │   ├── ConfidenceHistogram.tsx
    │   │   └── ModelCard.tsx
    │   └── types/
    │       └── api.ts                    ← TypeScript types mirroring API response shapes
    └── src/__tests__/
        ├── DetectionLogTable.test.tsx
        ├── FieldAnalysisChart.test.tsx
        ├── ConfidenceHistogram.test.tsx
        └── ModelCard.test.tsx
```

---

## Open Questions for Architect

1. **SPML dataset field names.** The HuggingFace dataset `reshabhs/SPML_Chatbot_Prompt_Injection` may use `prompt`/`label`, `text`/`label`, or another schema. The architect should document the inspection step and note the most likely field names based on the dataset card. The implementer confirms by inspecting before writing the data loader. This is a must-resolve before the data loader can be written.

2. **Confidence distribution data source.** The Confidence Distribution tab (Tab 3) shows a histogram of `injection_probability` scores, split by flagged vs benign. Two options: (a) add a `GET /logs/probabilities` endpoint that returns a flat list of `{probability, flagged}` objects and compute bins client-side in React; (b) compute bins server-side in `GET /logs/stats` and return them as part of the stats response. Architect should pick one and specify the response shape.

3. **Classifier startup failure mode.** If `MODEL_CHECKPOINT_DIR` is set but the files are missing, the lifespan should fail fast (raise an exception, preventing the app from starting) rather than logging a warning and serving 503. Architect confirms: fail-fast on startup vs lazy 503. Proposed answer: fail-fast — matches workspace convention (raise on uninitialised state).

4. **Proxy forwarding — request body passthrough.** `POST /proxy` receives a `DetectionRequest` body, but the downstream LLM expects its own format (e.g. OpenAI chat completions). Two options: (a) the proxy forwards the raw request body bytes as-is to `DOWNSTREAM_LLM_URL` (the caller is responsible for sending a body the downstream LLM understands); (b) the proxy wraps the `DetectionRequest` into a downstream-specific format. Proposed answer: (a) — forward raw body bytes. This keeps the proxy format-agnostic and production-realistic.

5. **async vs sync SQLAlchemy.** The service uses asyncpg. Architect confirms whether to use SQLAlchemy async sessions throughout (`AsyncSession`, `async with session.begin()`) or to use sync sessions in a thread pool. Proposed answer: async throughout — consistent with FastAPI async handlers.

---

## Handoff

Next role: architect

The architect reads this file and the brief output to:
- Define all data models (Pydantic request/response, SQLAlchemy ORM, training dataclasses) with exact field names and types.
- Define all module interfaces: every public function in the training project, every endpoint handler signature, every hook return type.
- Define the DB schema with indexes.
- Resolve the five open questions above.
- Specify the recharts component configuration for Field Analysis (bar chart) and Confidence Distribution (grouped bar chart).
- Define the lifespan startup sequence and classifier loading contract.

**Flags for architect:**
- OQ1 (SPML field names) is a blocker for the data loader. Architect must document the inspection step explicitly so the implementer knows what to do before writing `dataset.py`.
- OQ2 (confidence distribution data source) determines whether a new endpoint is needed or whether `/logs/stats` grows.
- OQ4 (proxy body passthrough) determines the httpx call signature in `detect.py`.
