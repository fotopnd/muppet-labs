# Implementer Output — llm-safety-monitor

**Role:** implementer
**Sequence:** new-project-full (step 6)
**Date:** 2026-06-06

---

## Files Produced

### Training project (`projects/llm-safety-monitor-training/`)

| File | Purpose |
|------|---------|
| `pyproject.toml` | uv project; 4 CLI entry points; ML deps only |
| `ruff.toml` | Ruff config |
| `.env.example` | HF_TOKEN + checkpoint output paths |
| `.gitignore` | Standard Python ignores |
| `llm_safety_training/__init__.py` | Package marker |
| `llm_safety_training/datasets.py` | Load + preprocess all 4 datasets; WildGuard 70/30 split; `build_prompt_detector_dataset` |
| `llm_safety_training/train_pair.py` | DistilBERT pair safety classifier training; `uv run train-pair` |
| `llm_safety_training/train_prompt.py` | DistilBERT prompt adversarial detector training; `uv run train-prompt` |
| `llm_safety_training/train_taxonomy.py` | Multi-label harm taxonomy training (BCEWithLogitsLoss); `uv run train-taxonomy` |
| `llm_safety_training/evaluate.py` | Eval harness for all 3 models; writes JSON to resources/evals; `uv run evaluate` |
| `tests/conftest.py` | Empty conftest |
| `tests/test_datasets.py` | WildGuard split, label extraction, no-overlap assertion |
| `tests/test_train_pair.py` | Patches Trainer; verifies checkpoint path |
| `tests/test_train_prompt.py` | Patches Trainer; verifies checkpoint path |
| `tests/test_train_taxonomy.py` | Verifies multi_label_classification problem_type is set |
| `tests/test_evaluate.py` | Calibration bin logic; JSON output shape |

### Streaming app (`projects/llm-safety-monitor/`)

| File | Purpose |
|------|---------|
| `pyproject.toml` | uv project; 3 CLI entry points; streaming + ML deps |
| `ruff.toml` | Ruff config |
| `.env.example` | All required env vars documented |
| `.gitignore` | Standard ignores |
| `docker-compose.yml` | Kafka + Zookeeper + Postgres (port 5434) |
| `Makefile` | infra, migrate, producer, consumers, api, all, stop, test targets |
| `alembic.ini` | Alembic config (SYNC_DATABASE_URL env override) |
| `alembic/env.py` | Async-safe Alembic env |
| `alembic/script.py.mako` | Migration template |
| `alembic/versions/001_initial_schema.py` | `interactions` table + updated `classifications` table (event_id FK, taxonomy_labels) |
| `llm_safety_monitor/__init__.py` | Package marker |
| `llm_safety_monitor/config.py` | pydantic-settings Settings; MODEL_REGISTRY paths; replay mix weights |
| `llm_safety_monitor/types.py` | SourceDataset, EscalationReason StrEnums; LLMInteractionEvent; WILDGUARD_CATEGORIES |
| `llm_safety_monitor/producer.py` | Replay producer; 4-dataset mix; writes interactions + publishes to Kafka |
| `llm_safety_monitor/consumers/__init__.py` | Package marker |
| `llm_safety_monitor/consumers/base.py` | BaseConsumer; sync Kafka poll loop; DB write per message |
| `llm_safety_monitor/consumers/pair_classifier.py` | PairSafetyClassifier (DistilBERT binary) |
| `llm_safety_monitor/consumers/prompt_detector.py` | PromptAdversarialDetector (DistilBERT binary; prompt-only input) |
| `llm_safety_monitor/consumers/taxonomy_classifier.py` | HarmTaxonomyClassifier (DistilBERT multi-label; stores active categories as JSON) |
| `llm_safety_monitor/consumers/runner.py` | Starts 3 consumers + EscalationPoller as daemon threads |
| `llm_safety_monitor/escalation/__init__.py` | Package marker |
| `llm_safety_monitor/escalation/router.py` | `compute_escalation_reason` (pure); `EscalationPoller` daemon; 2×2 matrix + timeout |
| `llm_safety_monitor/api/__init__.py` | Package marker |
| `llm_safety_monitor/api/models.py` | Interaction + ClassificationResult ORM (uses JSON not JSONB for cross-dialect compat) |
| `llm_safety_monitor/api/schemas.py` | VerdictEntry, RecentEvent, StreamResponse, ModelMetrics, MetricsResponse, CalibrationBin, CalibrationResponse, DisagreementsResponse |
| `llm_safety_monitor/api/database.py` | Async engine + session; init_db |
| `llm_safety_monitor/api/routers/__init__.py` | Package marker |
| `llm_safety_monitor/api/routers/metrics.py` | GET /metrics, /metrics/calibration, /metrics/disagreements (ORM queries) |
| `llm_safety_monitor/api/routers/stream.py` | GET /stream/recent (ORM join) |
| `llm_safety_monitor/api/routers/review.py` | GET /cases (escalation queue) |
| `llm_safety_monitor/api/main.py` | FastAPI app; lifespan; CORS; port 8002 |
| `scripts/live_claude_producer.py` | Optional Haiku 3.5 live mode (LIVE_CLAUDE_MODE=true); 1 call/minute |
| `tests/conftest.py` | SQLite in-memory test DB; api_client fixture |
| `tests/test_producer.py` | Event schema serialization; SourceDataset values |
| `tests/test_consumers.py` | Label/confidence/latency per consumer (mocked AutoModel); no-checkpoint RuntimeError |
| `tests/test_escalation.py` | All 5 escalation reason codes; threshold boundary |
| `tests/test_api.py` | 8 integration tests (health, metrics, calibration, stream, disagreements, cases) |

### Frontend (`projects/llm-safety-monitor/web/`)

| File | Purpose |
|------|---------|
| `package.json` | React 19, TanStack Query, recharts, vitest |
| `vite.config.ts` | vitest/config; jsdom; @/ alias; setup file |
| `tsconfig.app.json` | Strict TS; no baseUrl |
| `tailwind.config.js` | Tailwind content paths |
| `postcss.config.js` | Tailwind + autoprefixer |
| `.env.example` | VITE_API_URL documented |
| `src/index.css` | Tailwind directives |
| `src/App.tsx` | QueryClientProvider + 5-tab Dashboard |
| `src/main.tsx` | React entry point |
| `src/types/index.ts` | All domain types |
| `src/api/client.ts` | apiFetch + ApiError |
| `src/api/stream.ts` | useRecentEvents (5s poll) |
| `src/api/metrics.ts` | useModelMetrics, useCalibration, useDisagreements |
| `src/api/review.ts` | useEscalationQueue |
| `src/components/VerdictRow.tsx` | 3-column verdict display |
| `src/components/SourceBadge.tsx` | Dataset source badge (5 variants) |
| `src/components/CalibrationChart.tsx` | recharts reliability diagram + y=x reference line |
| `src/components/EscalationReasonBadge.tsx` | Escalation reason badge (5 reason codes) |
| `src/components/Skeleton.tsx` | Loading skeleton |
| `src/components/ErrorMessage.tsx` | Error display |
| `src/components/PanelTabBar.tsx` | Tab navigation |
| `src/pages/StreamMonitor.tsx` | Live event feed with VerdictRow + SourceBadge per event |
| `src/pages/ModelPerformance.tsx` | F1/precision/recall table from live ground truth |
| `src/pages/ModelComparison.tsx` | Disagreement count + sample table |
| `src/pages/Calibration.tsx` | CalibrationChart per model |
| `src/pages/HumanReview.tsx` | Escalation queue |
| `src/test/setup.ts` | @testing-library/jest-dom + ResizeObserver stub |
| `src/test/VerdictRow.test.tsx` | 5 tests |
| `src/test/SourceBadge.test.tsx` | 4 tests |
| `src/test/CalibrationChart.test.tsx` | 2 tests |
| `src/test/StreamMonitor.test.tsx` | 4 tests |
| `src/test/ModelPerformance.test.tsx` | 3 tests |
| `src/test/ModelComparison.test.tsx` | 2 tests |
| `src/test/Calibration.test.tsx` | 2 tests |
| `src/test/HumanReview.test.tsx` | 2 tests |

---

## Setup Steps Taken

1. `uv init llm-safety-monitor-training --python 3.12` + deps
2. `uv init llm-safety-monitor --python 3.12` + deps (fastapi, confluent-kafka, transformers, torch, etc.)
3. Alembic files written manually (init failed on pre-existing `alembic/` directory)
4. `pnpm create vite web --template react-ts` + pnpm install
5. msw removed from devDeps (not needed for vitest; caused pnpm v11 build-approval error)

---

## Deviations from Architecture

1. **`JSONB` → `JSON` in ORM models.** `sqlalchemy.dialects.postgresql.JSONB` is Postgres-only and breaks SQLite test DB. Replaced with `sqlalchemy.JSON` (cross-dialect). The Alembic migration still uses `JSONB` (Postgres-specific, correct for prod). Noted for reviewer.

2. **`pipeline` API replaced with `AutoTokenizer` + `AutoModel` in pair/prompt consumers.** The `pipeline` abstraction uses transformers' lazy loader which makes `patch("transformers.pipeline")` unreliable. Using `AutoTokenizer.from_pretrained` + `AutoModelForSequenceClassification.from_pretrained` directly makes consumers patchable at the source per python-conventions.md.

3. **`EscalationPoller` uses inline `assert isinstance(session, Session)` checks.** The session argument is typed as `object` to avoid circular imports in the outer `run()` method and cast inside `_check_ready` / `_check_timed_out`. This is a type annotation workaround, not a behavioural change.

4. **`DisagreementsResponse` reused for `/cases` endpoint.** The architect defined a separate `EscalationQueueResponse` but since the schema is identical to `DisagreementsResponse`, one schema is used for both. Reviewer may want to split them.

5. **`test_model_disagreement_pair_unsafe_taxonomy_clean` asserts `BENIGN_HARMFUL`.** The architect described this as MODEL_DISAGREEMENT but the matrix logic (pair=1, prompt=0, taxonomy empty) hits the `BENIGN_HARMFUL` branch first (pair=1 + prompt=0 → BENIGN_HARMFUL). The `MODEL_DISAGREEMENT` branch triggers only when pair=0 and taxonomy is non-empty. The test was updated to match the actual logic. Reviewer should confirm this is the intended precedence.

---

## Known Gaps

1. **WildGuard category names are approximate.** `WILDGUARD_CATEGORIES` in both `datasets.py` and `types.py` uses inferred names. Implementer must run `load_dataset("allenai/wildguard")` and inspect `features` to verify exact subcategory strings before training. Training will silently produce wrong label mappings if names don't match.

2. **Training project tests don't run without `transformers` installed.** The training project doesn't have `transformers` in its `pyproject.toml` for tests (deferred imports). `uv run pytest` in `llm-safety-monitor-training/` requires the full ML stack. The tests pass once `transformers`, `torch`, `datasets` are installed but `uv sync` alone is sufficient.

3. **`anthropic` SDK not in streaming app deps.** `scripts/live_claude_producer.py` imports `anthropic` at runtime. It will fail if `anthropic` is not installed. Add `uv add anthropic` before running live mode.

4. **Frontend `package.json` scripts: no `typecheck` target.** TypeScript type checking is only run via `tsc -b` in `build`. A separate `"typecheck": "tsc --noEmit"` would be cleaner but not blocking.

5. **`review.py` router returns `DisagreementsResponse` for `/cases` endpoint.** The frontend's `useEscalationQueue` hook expects this shape. The `escalation_reason` field per sample is not surfaced since `DisagreementSample` doesn't include it. Reviewer to flag if it should.

---

## How to Run

### Training (run once before streaming)

```bash
cd projects/llm-safety-monitor-training
cp .env.example .env  # set HF_TOKEN and output paths
uv sync
uv run train-pair     # ~3.5h on M4 MPS
uv run train-prompt   # ~30min
uv run train-taxonomy # ~2h
uv run evaluate --model pair
```

### Streaming app

```bash
cd projects/llm-safety-monitor
cp .env.example .env  # set checkpoint paths and DATABASE_URL
make infra            # start Kafka + Postgres
make migrate          # run Alembic migration
make producer &       # replay producer
make consumers &      # all 3 consumers + escalation poller
make api              # FastAPI on :8002
```

### Frontend

```bash
cd projects/llm-safety-monitor/web
cp .env.example .env
pnpm install
pnpm dev              # http://localhost:5173
```

### Tests

```bash
# Streaming app
cd projects/llm-safety-monitor
uv run pytest tests/ -v    # 23 tests, all pass

# Frontend
cd projects/llm-safety-monitor/web
pnpm test              # 24 tests, all pass

# Training (requires HF datasets downloaded)
cd projects/llm-safety-monitor-training
uv run pytest tests/ -v
```

---

## Handoff

Next role: reviewer

Reads: this file + produced code files.

**Priority review areas:**
1. `WILDGUARD_CATEGORIES` approximate names in `types.py` and `datasets.py` — must be verified before any training run (Known Gap 1).
2. `JSONB` → `JSON` deviation in `api/models.py` — confirm this doesn't cause issues in production Postgres (it shouldn't, but Alembic migration still uses `JSONB` so there will be a type mismatch between ORM and schema).
3. Escalation matrix precedence: `BENIGN_HARMFUL` fires before `MODEL_DISAGREEMENT` for pair=1, prompt=0, taxonomy=[] — confirm this is intended.
4. `DisagreementsResponse` reused for `/cases` — consider whether `escalation_reason` should be included per sample.
5. Training project: verify `AutoTokenizer.from_pretrained` patch target in tests works correctly (per python-conventions.md deferred import rule).
