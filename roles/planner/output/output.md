# Planner Output — llm-safety-monitor

**Date:** 2026-06-06
**Sequence:** new-project-full (v3 of moderation-dashboard — substantial rework)
**Role executing:** planner

---

## Resolutions to Brief Open Questions

Before requirements: these are the five planner decisions the brief explicitly requested.

**Q1 — Prompt classifier training size:** Accept ~6k balanced examples. No augmentation with HarmBench or SALAD-Bench. The narrative is: "We tested whether a small, focused adversarial dataset (AdvBench + JailbreakBench + WildGuard harmful prompts) is sufficient for a binary prompt safety classifier." The held-out eval tells the real story. Augment only as a contingency if held-out F1 falls below 0.70 — that contingency is noted but not part of the planned implementation.

**Q2 — HH-RLHF input format:** Extract final human turn + final assistant turn, not the full conversation history. The `chosen`/`rejected` fields are formatted multi-turn strings; parsing to the final pair keeps inputs within 512 tokens reliably and mirrors the actual prompt/response structure the pair classifier is meant to evaluate. Concatenate as: `[final human turn] + " [SEP] " + [final assistant turn]`.

**Q3 — WildGuard allocation:** Split at the example level with a fixed random seed (seed=42). 70% of WildGuard examples → pair classifier training set. 30% → taxonomy classifier training set. No example appears in both training sets. Each allocation's held-out eval set is drawn from a reserved 10% within that allocation before the split. This eliminates cross-classifier leakage and keeps evals meaningful.

**Q4 — Replay producer mix:** Fixed in config, with env-var override. No frontend control. The `.env.example` documents `REPLAY_MIX_HHRLHF=0.60`, `REPLAY_MIX_WILDGUARD=0.25`, `REPLAY_MIX_ADVBENCH=0.10`, `REPLAY_MIX_JAILBREAKBENCH=0.05`. Configurable is impressive but the frontend complexity cost is not worth it given the dashboard scope.

**Q5 — response_text storage:** New `interactions` table, not a column on `classifications`. Ground truth is event-level data, not prediction-level. Storing `ground_truth_safe` and `ground_truth_categories` three times per event (once per classifier) is wrong. The `interactions` table stores: event_id, prompt_text, response_text (nullable), source_dataset, ground_truth_safe (nullable bool), ground_truth_categories (JSONB, nullable). The `classifications` table gains an `event_id` FK column (nullable, for backward compat with existing seeded rows).

---

## Project

**llm-safety-monitor** — A streaming LLM safety classification platform that runs a continuous replay of real LLM interaction datasets through three purpose-trained safety classifiers, routes flagged interactions via a 2×2 prompt/response verdict matrix, and surfaces classifier agreement, calibration, and model disagreement on a five-tab React dashboard.

---

## Requirements

### Training Pipeline

1. `uv run train-pair` trains a DistilBERT pair safety classifier on HH-RLHF (primary) + WildGuard 70%-allocation (secondary). Training completes on Apple M4 MPS with batch_size=128. Checkpoint saved to `resources/models/llm-safety-monitor/pair-classifier-<YYYY-MM-DD>/`.
2. `uv run train-prompt` trains a DistilBERT prompt adversarial detector on AdvBench + JailbreakBench + WildGuard harmful prompts (positives) vs HH-RLHF chosen-side openers + WildGuard safe prompts (negatives), balanced to ~6k total. Checkpoint saved to `resources/models/llm-safety-monitor/prompt-detector-<YYYY-MM-DD>/`.
3. `uv run train-taxonomy` trains a DistilBERT multi-label harm taxonomy classifier on WildGuard 30%-allocation, 13-category BCEWithLogitsLoss head. Checkpoint saved to `resources/models/llm-safety-monitor/taxonomy-classifier-<YYYY-MM-DD>/`.
4. `uv run evaluate --model pair|prompt|taxonomy` evaluates the named model on its held-out split and writes a JSON eval report to `resources/evals/llm-safety-monitor/<model>-<timestamp>.json`. Report includes: F1, precision, recall (pair/prompt); per-category F1 and macro F1 (taxonomy); and per-confidence-bin actual positive rate for calibration diagram data.
5. WildGuard split: 70% allocated to pair classifier, 30% to taxonomy classifier, at example level with seed=42. Each allocation's held-out eval set is drawn from a 10% reserve within that allocation before the split. No WildGuard example appears in more than one training set.
6. Each `train_*.py` script has a test that patches `transformers.Trainer.train` and `transformers.Trainer.save_model`, verifies the checkpoint path argument is correct, and verifies the training loop is entered.

### Streaming Pipeline

7. `uv run producer` samples all four datasets at the configured mix (default 60/25/10/5), publishes one `LLMInteractionEvent` to Kafka every ~3 seconds. Mix is controlled by env vars documented in `.env.example`. Producer runs indefinitely until interrupted.
8. Each published event carries: `event_id` (UUID), `prompt` (str), `response` (str | None), `source_dataset` (literal), `ground_truth_safe` (bool | None), `ground_truth_categories` (list[str] | None).
9. `uv run consumers` starts all three classifiers (pair, prompt, taxonomy) as parallel threads. Each consumer subscribes to the same Kafka topic in the shadow consumer group so all three see every event.
10. Each consumer loads its model checkpoint at startup. If the checkpoint path does not exist or is not set in config, the consumer raises `RuntimeError` — no silent default or pending_weights fallback.
11. Each consumer writes one row to `classifications` per event: `event_id` (FK to interactions), `model_name`, `predicted_label` (int), `confidence` (float), `latency_ms` (float), `processed_at`.
12. The replay producer writes one row to `interactions` per event before publishing to Kafka: `event_id`, `prompt_text`, `response_text` (nullable), `source_dataset`, `ground_truth_safe` (nullable), `ground_truth_categories` (JSONB nullable), `created_at`.

### Escalation

13. The escalation router reads the pair classifier result and taxonomy classifier result for each event after both complete. It applies the 2×2 matrix and posts to case-queue with one of these reason codes: `BENIGN_HARMFUL` (pair unsafe + prompt benign), `JAILBREAK` (pair unsafe + prompt adversarial), `LOG_ONLY` (pair safe + prompt adversarial — log only, no case-queue post), `MODEL_DISAGREEMENT` (pair and taxonomy results contradict each other).
14. Prompt-only events (response is None) with prompt detector confidence > 0.7 produce `ADVERSARIAL_PROMPT_FLAGGED` escalation at medium severity.
15. Escalation logic waits for both pair and taxonomy results before running. Timeout: 10 seconds. If either result is absent after timeout, escalation skips the event and logs a warning with `exc_info=False`.

### Database

16. A new `interactions` table is created via Alembic migration: `id` (UUID PK), `prompt_text` (TEXT), `response_text` (TEXT nullable), `source_dataset` (VARCHAR), `ground_truth_safe` (BOOLEAN nullable), `ground_truth_categories` (JSONB nullable), `created_at` (TIMESTAMPTZ).
17. `classifications` table gains `event_id` (UUID, FK→interactions.id, nullable, indexed) via the same migration. Existing seeded rows have `event_id = NULL`.
18. Both schema changes ship as a single Alembic migration file.

### API

19. `GET /metrics` returns per-model F1, precision, recall, and sample count computed against live-stream events where `ground_truth_safe IS NOT NULL` (i.e. `event_id IS NOT NULL`). Response schema: `{ models: ModelMetrics[] }`.
20. `GET /metrics/calibration` returns per-model calibration data: 10 equal-width confidence bins (0–1), each with `bin_lower`, `bin_upper`, `count`, `actual_positive_rate`. Only bins with count > 0 are returned.
21. `GET /stream/recent?limit=50` returns the last N events ordered by `created_at` descending: `event_id`, `prompt_text` (truncated 200 chars), `response_text` (truncated 200 chars, nullable), `source_dataset`, `verdicts` (one entry per model with `model_name`, `predicted_label`, `confidence`), `escalation_level` (nullable string).
22. `GET /metrics/disagreements` is retained from the existing implementation (carried over unchanged).
23. All endpoints have at least one seeded-data test asserting computed output values. The `/metrics` test seeds 10 interactions with known `ground_truth_safe` values, seeds 10 matching classifications, and asserts F1 is non-zero and correct.

### Dashboard

24. StreamMonitor tab: renders recent events as a feed. Each item shows: prompt text (truncated), response text (truncated or "(no response)"), a `SourceBadge`, and a `VerdictRow` (three columns: pair verdict, prompt verdict, taxonomy category badges). Polls `GET /stream/recent` every 5 seconds.
25. ModelPerformance tab: renders per-model F1, precision, recall from live-stream ground truth (`GET /metrics`). Includes a static comparison column with held-out test-set F1 embedded at build time from the eval JSON (no runtime fetch for static data).
26. ModelComparison tab: renders pairwise agreement rate between all three classifier pairs, plus a samples table of recent disagreement events. Sources from `GET /metrics/disagreements`.
27. Calibration tab (new): renders a reliability diagram per model using recharts `LineChart` with a y=x reference line. Sources from `GET /metrics/calibration`. One chart per model; confidence bins on x-axis, actual positive rate on y-axis.
28. HumanReview tab: renders escalated events with `EscalationReasonBadge`, prompt + response text, per-model verdict, and approve/reject buttons. Updated with new reason codes from requirement 13.
29. Live Claude API mode: when `LIVE_CLAUDE_MODE=true` env var is set, a standalone script (`scripts/live_claude_producer.py`) sends benign prompts to Haiku 3.5, receives responses, and injects the pair as `source_dataset="live"` with `ground_truth_safe=None`. Off by default; runs as a separate process.

### Testing

30. Each consumer module has a test that mocks the model pipeline and verifies: `predicted_label` is 0 or 1, `confidence` is a float in [0,1], `latency_ms` is positive.
31. `test_escalation.py` has one test per escalation reason code (5 tests total), verifying correct code output from the 2×2 matrix inputs.
32. Each dashboard page has a vitest test suite. New components `VerdictRow`, `CalibrationChart`, and `SourceBadge` each have a dedicated unit test file.
33. Frontend mock objects for any types with required fields must be updated whenever required fields are added.

---

## Technology Stack

### Training (`projects/llm-safety-monitor-training/`)

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | Workspace standard |
| Package manager | uv | Workspace standard |
| Formatter/linter | ruff | Workspace standard |
| ML framework | transformers 5.x + torch (MPS) | Proven on this hardware for DistilBERT fine-tuning |
| Accelerator | accelerate | Required by transformers.Trainer ≥5.x |
| Dataset loading | datasets (HuggingFace) | All 4 datasets on Hub |
| Multi-label loss | BCEWithLogitsLoss (torch) | Taxonomy classifier 13-label head |
| Eval metrics | scikit-learn | F1, precision, recall, calibration curve |
| Testing | pytest | Workspace standard |

### Streaming App (`projects/llm-safety-monitor/`)

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | Workspace standard |
| Package manager | uv | Workspace standard |
| Formatter/linter | ruff | Workspace standard |
| Kafka client | confluent-kafka | Carried over |
| API framework | FastAPI + uvicorn | Carried over |
| ORM | SQLAlchemy 2.x (async) | Carried over |
| DB driver | asyncpg | Carried over |
| Schema management | Alembic | Carried over |
| Data validation | Pydantic v2 + pydantic-settings | Carried over |
| HTTP client (Claude) | anthropic SDK | Live Claude API mode (scripts only) |
| Testing | pytest + httpx + pytest-asyncio | Carried over |

### Frontend (`projects/llm-safety-monitor/web/`)

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | TypeScript 5.x | Workspace standard |
| Package manager | pnpm | Workspace standard |
| Bundler | Vite | Carried over |
| Framework | React 18 | Carried over |
| Data fetching | TanStack Query | Carried over |
| UI library | shadcn/ui (Tailwind) | Carried over |
| Charts | recharts 2.x | Already in project; CalibrationChart uses LineChart |
| Testing | vitest + @testing-library/react | Carried over |

---

## File and Module Structure

```
projects/
├── llm-safety-monitor-training/         ← NEW uv project (ML-heavy deps separate from app)
│   ├── pyproject.toml
│   ├── ruff.toml
│   ├── uv.lock
│   ├── .env.example                     ← HF_TOKEN, PAIR_CHECKPOINT_OUT, etc.
│   ├── llm_safety_training/
│   │   ├── __init__.py
│   │   ├── datasets.py                  ← load + preprocess all 4 datasets; WildGuard split logic
│   │   ├── train_pair.py                ← pair classifier training + CLI entry point
│   │   ├── train_prompt.py              ← prompt adversarial detector training + CLI entry point
│   │   ├── train_taxonomy.py            ← harm taxonomy (multi-label) training + CLI entry point
│   │   └── evaluate.py                  ← eval harness CLI; writes JSON to resources/evals/
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_datasets.py             ← WildGuard split ratios, label extraction, format
│       ├── test_train_pair.py           ← patches Trainer; verifies checkpoint path arg
│       ├── test_train_prompt.py
│       ├── test_train_taxonomy.py
│       └── test_evaluate.py             ← patches model load; verifies JSON output schema
│
└── llm-safety-monitor/                  ← NEW uv project (streaming app + frontend)
    ├── pyproject.toml
    ├── ruff.toml
    ├── uv.lock
    ├── alembic.ini
    ├── docker-compose.yml               ← Kafka + Zookeeper + Postgres (port 5434)
    ├── Makefile                         ← producer, consumers, api, all, stop targets
    ├── .env.example                     ← all required env vars documented
    ├── alembic/
    │   ├── env.py
    │   └── versions/
    │       └── 001_initial_schema.py    ← interactions table + classifications.event_id FK
    ├── llm_safety_monitor/
    │   ├── __init__.py
    │   ├── config.py                    ← Settings; MODEL_REGISTRY for 3 classifiers
    │   ├── types.py                     ← LLMInteractionEvent Pydantic model; SourceDataset StrEnum
    │   ├── producer.py                  ← replay producer (4-dataset mix, env-var configurable)
    │   ├── consumers/
    │   │   ├── __init__.py
    │   │   ├── base.py                  ← BaseConsumer (adapted from moderation-dashboard)
    │   │   ├── pair_classifier.py       ← PairSafetyClassifier (binary)
    │   │   ├── prompt_detector.py       ← PromptAdversarialDetector (binary)
    │   │   ├── taxonomy_classifier.py   ← HarmTaxonomyClassifier (multi-label, 13 heads)
    │   │   └── runner.py                ← starts all 3 consumers in parallel threads
    │   ├── escalation/
    │   │   └── router.py                ← 2×2 matrix; EscalationReason StrEnum; case-queue POST
    │   └── api/
    │       ├── __init__.py
    │       ├── models.py                ← Interaction ORM + updated ClassificationResult ORM
    │       ├── schemas.py               ← Pydantic response schemas
    │       ├── database.py              ← async engine + session factory
    │       ├── main.py                  ← FastAPI app, lifespan, CORS, routers
    │       └── routers/
    │           ├── __init__.py
    │           ├── metrics.py           ← /metrics, /metrics/calibration, /metrics/disagreements
    │           ├── stream.py            ← /stream/recent
    │           └── review.py            ← /cases (escalation queue, carried over)
    ├── scripts/
    │   └── live_claude_producer.py      ← optional live Haiku 3.5 mode; off by default
    ├── tests/
    │   ├── __init__.py
    │   ├── conftest.py                  ← test DB, api_client, seeded interactions fixture
    │   ├── test_producer.py             ← mix sampling, event schema, Kafka publish (mocked)
    │   ├── test_consumers.py            ← label/confidence/latency per consumer (mocked pipeline)
    │   ├── test_escalation.py           ← 5 tests: one per escalation reason code
    │   └── test_api.py                  ← integration tests for all endpoints with seeded data
    └── web/
        ├── package.json
        ├── pnpm-lock.yaml
        ├── vite.config.ts
        ├── tsconfig.app.json
        ├── tailwind.config.js
        ├── .env.example                 ← VITE_API_URL documented
        └── src/
            ├── main.tsx
            ├── App.tsx                  ← 5-tab routing
            ├── index.css
            ├── types/
            │   └── index.ts             ← LLMInteractionEvent, VerdictRow, CalibrationBin, EscalationEntry
            ├── api/
            │   ├── client.ts            ← apiFetch base
            │   ├── stream.ts            ← useRecentEvents()
            │   ├── metrics.ts           ← useModelMetrics(), useCalibration(), useDisagreements()
            │   └── review.ts            ← useEscalationQueue(), useDecide()
            ├── components/
            │   ├── VerdictRow.tsx        ← NEW: 3-column verdict display
            │   ├── SourceBadge.tsx       ← NEW: dataset source badge (4 variants)
            │   ├── CalibrationChart.tsx  ← NEW: recharts reliability diagram
            │   ├── EscalationReasonBadge.tsx ← NEW: reason code badge
            │   ├── Skeleton.tsx          ← carried over
            │   ├── ErrorMessage.tsx      ← carried over
            │   └── PanelTabBar.tsx       ← carried over
            ├── pages/
            │   ├── StreamMonitor.tsx     ← reworked: VerdictRow + SourceBadge per event
            │   ├── ModelPerformance.tsx  ← reworked: live F1 vs held-out F1 columns
            │   ├── ModelComparison.tsx   ← reworked: 3-way pairwise agreement
            │   ├── Calibration.tsx       ← NEW: CalibrationChart per model
            │   └── HumanReview.tsx       ← updated: new escalation reason codes
            └── test/
                ├── setup.ts
                ├── StreamMonitor.test.tsx
                ├── ModelPerformance.test.tsx
                ├── ModelComparison.test.tsx
                ├── Calibration.test.tsx   ← NEW
                ├── HumanReview.test.tsx
                ├── VerdictRow.test.tsx    ← NEW
                ├── CalibrationChart.test.tsx ← NEW
                └── SourceBadge.test.tsx   ← NEW
```

**Workspace outputs** (written by training scripts, read by consumers via config):
```
resources/
├── models/
│   └── llm-safety-monitor/
│       ├── pair-classifier-<date>/
│       ├── prompt-detector-<date>/
│       └── taxonomy-classifier-<date>/
└── evals/
    └── llm-safety-monitor/
        ├── pair-<timestamp>.json
        ├── prompt-<timestamp>.json
        └── taxonomy-<timestamp>.json
```

---

## Open Questions for Architect

Each question includes a proposed answer. Architect confirms or overrides.

1. **Calibration endpoint response schema:** Proposed: `{ models: [{ model_name: str, bins: [{ bin_lower: float, bin_upper: float, count: int, actual_positive_rate: float }] }] }`. 10 bins, zero-count bins excluded. Computed for all three models. Architect to confirm and specify whether `actual_positive_rate` is undefined (omitted) vs `null` for bins excluded by the count filter.

2. **Taxonomy categories enum:** WildGuard uses 13 named harm categories. Proposed: define as a `StrEnum` (`HarmCategory`) in `llm_safety_monitor/types.py`. Names taken from WildGuard dataset card (architect to verify exact names from the dataset schema). This enum is shared by the taxonomy consumer, the escalation router, and the API schemas.

3. **Escalation result coordination across consumers:** Proposed: after each classification write, the writer queries the DB for whether both `pair_classifier` and `taxonomy_classifier` rows exist for the same `event_id`. If both are present and the escalation has not yet been triggered (needs an `escalated` flag on `interactions`), fire the escalation. This requires an `escalated BOOLEAN DEFAULT FALSE` column on `interactions`. Architect to confirm this approach or propose an alternative.

4. **Replay producer in-memory state:** Proposed: load all dataset examples into memory at startup, shuffle per-dataset with seed=None (random each run), then `itertools.cycle` over each shuffled list. The weighted mix is achieved by sampling from a distribution across the four cycled iterators each tick. No persistent cursor. Architect to confirm memory is safe (262k examples × ~500 bytes avg = ~130MB, well within 24GB).

5. **Taxonomy consumer output format:** The taxonomy classifier outputs 13 confidence scores. Proposed: `predicted_label` in `classifications` stores the JSON-encoded list of active category names (categories above 0.5 threshold), and `confidence` stores the mean sigmoid confidence across all 13 heads. Architect to decide whether to store full per-category scores separately or use this compact representation.

---

## Implementation Order

1. **Training** (`llm-safety-monitor-training/`): datasets.py first, then train_pair/train_prompt/train_taxonomy can run in parallel, then evaluate. Required before consumers can load checkpoints.
2. **DB schema** (Alembic migration): `interactions` table + `event_id` FK. Blocks all streaming components.
3. **Streaming types + config** (`types.py`, `config.py`): no dependencies.
4. **Producer** (`producer.py`): depends on types and Kafka.
5. **Consumers** (base → pair/prompt/taxonomy → runner): depend on checkpoints + types + DB schema.
6. **Escalation router** (`escalation/router.py`): depends on consumers writing to DB.
7. **API** (models → schemas → routers → main): depends on DB schema.
8. **Frontend** (types → api hooks → components → pages): depends on API.

---

## Handoff

Next role: architect

Reads: this file + `_config/project-state.md`.

Primary design tasks for architect:
- ORM models: `Interaction`, updated `ClassificationResult` (with `event_id` FK, `escalated` flag on interactions if Q3 confirmed)
- API schemas: `RecentEvent`, `ModelMetrics`, `CalibrationBin`, `CalibrationResponse`, `DisagreementResponse`
- Consumer interface: what `BaseConsumer.classify()` returns — pair and prompt return binary (label, confidence); taxonomy returns (list[HarmCategory], mean_confidence)
- Escalation router: internal coordination mechanism (DB-poll approach from Q3, or alternative)
- Frontend types: `LLMInteractionEvent`, `VerdictRow`, `CalibrationBin`, `EscalationEntry`

Flag: the taxonomy classifier's multi-label output (13 labels) needs a clear decision on how it flows through `classifications.predicted_label` and `confidence` — Q5 above provides a proposal, architect must decide.
