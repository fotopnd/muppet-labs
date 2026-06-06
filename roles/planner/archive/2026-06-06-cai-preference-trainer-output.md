# Planner Output — cai-preference-trainer

**Role:** planner
**Sequence:** `new-project-full` (step 2)
**Date:** 2026-06-06

---

## Project

`cai-preference-trainer` — a mini Constitutional AI pipeline comprising an annotation interface, preference dataset builder, DistilBERT reward model trainer, and 4-tab evaluation dashboard; demonstrating RLHF preference learning against Anthropic's 10 CAI principles.

---

## Brief Flags Resolved

**Flag: single RM vs. 10 separate RMs**
Decision: single DistilBERT model with principle index as text prefix ("Principle N: ..."). Rationale: one training run, smaller footprint, principle signal is captured in the input text. The architect defines the exact prefix format and input construction.

**Flag: TIE annotation handling**
Decision: TIE annotations are stored but excluded from RM training. Binary labels only: 0 = A preferred, 1 = B preferred. A three-class model is out of scope for v1.

**Flag: `cai-preference-trainer/` project structure**
Decision: separate uv project at `cai-preference-trainer/` (training CLI only), same pattern as `llm-safety-monitor-training/`. The FastAPI backend lives in `cai-preference-trainer-api/`. The frontend lives in `cai-preference-trainer-ui/`.

**Flag: Ollama pair generation**
Decision: CLI script at `cai-preference-trainer-api/scripts/generate_pairs.py` — manually triggered. Not an API endpoint. Ollama must be running locally.

**Flag: annotation UI placement**
Decision: same React SPA as dashboard, `/annotate` route. No separate build artifact.

**Flag: "annotated" definition for queue**
Decision: a pair is fully annotated when all 10 principle annotations have been submitted by the current annotator. The queue shows pairs where the current annotator has 0 annotations (first-pass queue). Pairs with partial annotations (1–9 principles rated) also appear in the queue with a "resume" indicator.

**Flag: HH-RLHF prompt extraction**
The `Anthropic/hh-rlhf` dataset has `chosen` and `rejected` fields. Each is a conversation string. Format: `"\n\nHuman: <prompt>\n\nAssistant: <response>"`. Extraction: split on `"\n\nAssistant: "`, take first segment after `"\n\nHuman: "` as prompt, take last assistant segment as response. Architect locks this into the ingestion function signature.

---

## Requirements

1. `POST /api/pairs/ingest-hhrlhf` — ingests up to `limit` chosen/rejected pairs from `Anthropic/hh-rlhf` (HuggingFace `datasets`); inserts into `response_pairs` with `source='hhrlhf'`; skips duplicates on `pair_id` collision.
2. `scripts/generate_pairs.py --prompts-file <path> --count <n>` — generates `n` pairs per prompt via Ollama `qwen2.5-coder:7b` at T=0.2 (response_a) and T=0.9 (response_b); inserts into `response_pairs` with `source='generated'`.
3. `GET /api/pairs/queue` — returns unannotated or partially-annotated pairs for the given `annotator_id`; sorted by `created_at` ascending; paginates with `limit` and `offset`.
4. `GET /api/pairs/{pair_id}` — returns full pair detail (prompt, response_a, response_b, source).
5. `POST /api/annotations` — accepts a batch of up to 10 principle annotations for a single pair from a single annotator; validates `principle_id` in 1–10 range; stores each as a separate `annotations` row; returns created annotation IDs.
6. `GET /api/stats/principle-coverage` — returns, for each of the 10 principles: `principle_id`, `annotation_count`, `agreement_rate` (% non-TIE annotations).
7. `GET /api/stats/rm-eval` — returns latest eval JSON from `resources/evals/cai-preference-trainer/`; parsed into per-principle accuracy and AUC-ROC.
8. `GET /api/stats/calibration` — returns calibration bin data per principle (10 bins); computed from latest eval JSON.
9. Annotation UI at `/annotate` — shows a pair picker (queue list), loads selected pair, renders 10 principle rows each with A/B/Tie radio + confidence 1–3 selector; Submit button posts all 10 ratings in one request.
10. Dashboard at `/` with 4 tabs: Annotation Queue, Principle Coverage, RM Eval, Calibration — all data via TanStack Query hooks with 30-second refetch on Annotation Queue and Principle Coverage.
11. `uv run train-rm --output-dir <path> --train-split 0.8` in `cai-preference-trainer/` — builds dataset from non-TIE annotations (minimum 50); trains DistilBERT binary classifier; saves checkpoint via `model.save_pretrained()`.
12. `uv run evaluate-rm --checkpoint-dir <path> --output-file <path>` — evaluates checkpoint on held-out 20% annotations; computes per-principle accuracy and AUC-ROC; writes JSON to `resources/evals/cai-preference-trainer/<timestamp>.json`.
13. Training requires at least 50 non-TIE annotations total; the CLI raises `ValueError` with a clear message if fewer annotations exist.
14. DB migrations managed via Alembic; `alembic upgrade head` applies the schema; migration files committed.
15. All API endpoints return structured JSON matching TypeScript types defined in the frontend.
16. pytest tests cover: HH-RLHF ingestion (mock `datasets.load_dataset`), annotation submit endpoint (seeded Postgres), principle coverage aggregation (seeded data asserts computed values), calibration bin computation, RM dataset builder (asserts TIEs excluded).

---

## Technology Stack

### API (cai-preference-trainer-api/)

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | Workspace standard |
| Package manager | uv | Workspace standard |
| Formatter/linter | ruff | Workspace standard |
| Web framework | FastAPI 0.111 | Async, OpenAPI generation, established workspace pattern |
| ORM | SQLAlchemy 2.x (async) | Type-safe ORM; async engine for FastAPI |
| DB driver | asyncpg | Async PostgreSQL driver |
| Migrations | Alembic | Standard SQLAlchemy migration tool |
| Validation | Pydantic v2 | FastAPI native integration |
| HuggingFace | datasets 2.x | HH-RLHF dataset loading |
| Ollama client | httpx (async) | HTTP calls to local Ollama server |
| Testing | pytest + pytest-asyncio + httpx | Async endpoint testing |

### Trainer (cai-preference-trainer/)

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | Workspace standard |
| Package manager | uv | Workspace standard |
| ML framework | transformers + accelerate | HuggingFace Trainer with MPS support |
| Base model | distilbert-base-uncased | Lightweight; established in workspace |
| Device | MPS auto-detection via Trainer | M4 24 GB; no `bf16`; no `no_cuda` flag |
| Eval metrics | scikit-learn (accuracy, roc_auc_score) | Standard classification metrics |
| Testing | pytest | Unit tests for dataset builder and calibration |

### Frontend (cai-preference-trainer-ui/)

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | TypeScript 5.x | Workspace standard |
| Package manager | pnpm | Workspace standard |
| Framework | React 18 + Vite | Established workspace pattern |
| Server state | TanStack Query v5 | API data fetching |
| UI components | shadcn/ui | Established workspace pattern |
| Charts | recharts | CalibrationChart, coverage bars |
| Routing | React Router v6 | `/` dashboard and `/annotate` route |
| Linting | eslint (flat config) + prettier | Workspace standard |
| Testing | vitest + @testing-library/react | Workspace standard |

---

## File and Module Structure

```
cai-preference-trainer-api/          ← FastAPI backend (uv project)
├── pyproject.toml
├── .env                             ← DB_URL, OLLAMA_BASE_URL (gitignored)
├── .env.example
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 0001_initial_schema.py
├── src/
│   └── cai_api/
│       ├── __init__.py
│       ├── main.py                  ← FastAPI app, router registration
│       ├── config.py                ← pydantic-settings Settings (extra="ignore")
│       ├── database.py              ← async engine, session factory, Base
│       ├── models/
│       │   ├── __init__.py
│       │   ├── response_pair.py     ← ResponsePair ORM model
│       │   └── annotation.py        ← Annotation ORM model
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── pair.py              ← ResponsePairCreate, ResponsePairOut, QueueItem
│       │   ├── annotation.py        ← AnnotationCreate, AnnotationOut, AnnotationBatch
│       │   └── stats.py             ← PrincipleCoverage, RMEvalResult, CalibrationResult
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── pairs.py             ← /api/pairs/* endpoints
│       │   ├── annotations.py       ← /api/annotations endpoint
│       │   └── stats.py             ← /api/stats/* endpoints
│       ├── services/
│       │   ├── __init__.py
│       │   ├── hhrlhf_ingestor.py   ← HH-RLHF dataset loading + insertion
│       │   ├── calibration.py       ← 10-bin calibration computation
│       │   └── eval_loader.py       ← reads latest eval JSON from resources/evals/
│       └── principles.py            ← PRINCIPLES: list[dict] — 10 static CAI principles
│
├── scripts/
│   └── generate_pairs.py            ← Ollama pair generator CLI
│
└── tests/
    ├── conftest.py                  ← async test DB fixtures
    ├── test_hhrlhf_ingestor.py
    ├── test_annotations.py
    ├── test_stats.py
    └── test_calibration.py

cai-preference-trainer/             ← Training uv project (separate from API)
├── pyproject.toml
├── .env                             ← DB_URL (read-only; annotations fetched from API DB)
├── .env.example
├── src/
│   └── cai_trainer/
│       ├── __init__.py
│       ├── dataset_builder.py       ← fetches non-TIE annotations, builds HF Dataset
│       ├── train.py                 ← train-rm CLI entry point
│       ├── evaluate.py              ← evaluate-rm CLI entry point
│       └── calibration.py           ← 10-bin calibration (shared logic, separate copy)
└── tests/
    ├── conftest.py
    ├── test_dataset_builder.py
    └── test_calibration.py

cai-preference-trainer-ui/          ← React frontend (pnpm project)
├── package.json
├── pnpm-lock.yaml
├── vite.config.ts
├── tsconfig.json
├── .env.example                     ← VITE_API_BASE_URL
├── src/
│   ├── main.tsx                     ← React root, Router
│   ├── App.tsx                      ← top-level route definitions
│   ├── api/
│   │   └── client.ts                ← base fetch wrapper
│   ├── hooks/
│   │   ├── useQueue.ts              ← TanStack Query hook for /api/pairs/queue
│   │   ├── usePair.ts               ← hook for /api/pairs/{pair_id}
│   │   ├── usePrincipleCoverage.ts
│   │   ├── useRMEval.ts
│   │   └── useCalibration.ts
│   ├── pages/
│   │   ├── Dashboard.tsx            ← 4-tab layout
│   │   └── Annotate.tsx             ← annotation UI page
│   ├── components/
│   │   ├── AnnotationForm.tsx       ← 10-principle annotation form
│   │   ├── PrincipleCoverage.tsx    ← coverage table/chart
│   │   ├── RMEvalCard.tsx           ← accuracy/AUC table + model card
│   │   ├── CalibrationChart.tsx     ← recharts calibration plot
│   │   └── QueueList.tsx            ← annotation queue list
│   └── types/
│       └── api.ts                   ← all TypeScript API response types
└── tests/
    └── (vitest + testing-library tests)
```

---

## Open Questions for Architect

1. **DB connection from trainer** — the `cai-preference-trainer/` training project needs to read annotations from the same Postgres DB. Should it connect directly to Postgres (read-only DB_URL in its `.env`), or should it call the API? Proposed answer: direct DB connection via SQLAlchemy (read-only). The trainer is a CLI tool run locally — no need to go through the API layer.

2. **Calibration data source** — calibration bins are computed at eval time (`evaluate-rm` CLI) and written into the eval JSON, then served by `GET /api/stats/calibration`. The API reads the latest eval JSON file. Is this the right split, or should the API recompute calibration from raw eval output? Proposed answer: compute at eval time, store in JSON — API is a reader only. Keeps the API stateless with respect to ML artifacts.

3. **Annotator ID flow** — the annotation UI needs an `annotator_id` to filter the queue and tag submissions. There is no login system. Proposed answer: `annotator_id` is a URL parameter or stored in `localStorage` after the first visit; the UI renders a "set your name" prompt on first load. Architect decides where state lives.

4. **Pair queue definition for partial annotations** — requirement 3 says partial-annotation pairs (1–9 principles rated) appear with a "resume" indicator. The API needs to return per-pair annotation counts per annotator, not just "annotated" vs "not". Architect defines the exact queue response shape.

5. **Principles static resource format** — the 10 principles are a static list used in the API (for validation), the trainer (as prefix text), and the frontend (for display). Architect decides: Python module constant, JSON file, or both?

---

## Handoff

**Next role:** architect

The architect reads this file to:
- Define all data models (Pydantic + SQLAlchemy ORM) for `ResponsePair` and `Annotation`
- Define all API contracts (request/response shapes, HTTP methods, status codes)
- Define all function signatures in the API services and trainer modules
- Define TypeScript types for all API responses
- Define frontend hook signatures and component prop types
- Resolve the 5 open questions above
- Define the DB schema (tables, columns, types, indexes, constraints)
- Specify the exact input format for the RM (`"Principle N: [principle text] [SEP] prompt [SEP] response_a [SEP] response_b"`) and confirm tokenisation strategy

**Flags for architect:**
- OQ3 (annotator ID flow) drives whether the frontend has a settings page or just a localStorage pattern — this determines if an additional React component is needed.
- OQ4 (queue response shape) will require a SQL subquery or lateral join — flag if complexity is higher than expected.
- The single RM with principle prefix means the training dataset has `10x` the rows of the raw annotation count (one row per annotation per non-TIE principle). Architect should confirm this is the correct interpretation or if per-pair averaging is expected.
