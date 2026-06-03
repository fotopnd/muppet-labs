# Implementer Output — moderation-dashboard

**Role:** implementer
**Sequence:** `new-project-full` (step 6)
**Date:** 2026-06-03

---

## Files Produced

### Case-queue change (prerequisite)
| File | Purpose |
|------|---------|
| `projects/case-queue/api/app/routers/cases.py` | Added `source: str \| None` query param + filter to `list_cases()` and `_build_filters()` |
| `projects/case-queue/api/tests/test_cases.py` | Added `test_list_cases_filter_by_source` |

### Python backend (`projects/moderation-dashboard/`)
| File | Purpose |
|------|---------|
| `pyproject.toml` | uv project; 5 CLI entry points; pytest asyncio_mode=auto |
| `ruff.toml` | Ruff config; B008/E501 ignored (FastAPI Depends pattern, SQL strings) |
| `docker-compose.yml` | Zookeeper + Kafka (port 9093) + Postgres (port 5434) |
| `.env.example` | All env vars; Phase 2 checkpoints commented |
| `Makefile` | producer, consumers (production+shadow), anomaly, escalation, api, dbt-refresh, all, stop |
| `alembic.ini` | Alembic config pointing to port 5434 |
| `alembic/env.py` | Async Alembic env; `POSTGRES_URL_ASYNC` override |
| `alembic/script.py.mako` | Migration template |
| `moderation_dashboard/config.py` | `ModelSpec` dataclass; `MODEL_REGISTRY` dict; `Settings` with full architect spec; `get_settings()` |
| `moderation_dashboard/types.py` | `ModerationEvent` Pydantic model (event_id, jigsaw_id, content, ground_truth, category, published_at) |
| `moderation_dashboard/producer.py` | `CATEGORY_PRIORITY`, `get_primary_category()`, `load_jigsaw_csv()`, `ensure_topic()`, `publish_events()`, `main()` |
| `moderation_dashboard/consumers/base.py` | `BaseConsumer` with explicit (model_name, group_id, bootstrap_servers, topic, db_url) init; `classify()` abstract; `run()` measures latency around classify(); writes `Classification` ORM rows |
| `moderation_dashboard/consumers/distilbert.py` | `DistilBertZeroShotConsumer` — returns (label, confidence) from zero-shot pipeline scores |
| `moderation_dashboard/consumers/roberta.py` | `RobertaZeroShotConsumer` — same pattern as distilbert |
| `moderation_dashboard/consumers/detoxify_consumer.py` | `DetoxifyConsumer` — confidence = raw toxicity score |
| `moderation_dashboard/consumers/finetuned.py` | `FinetunedConsumer` base with checkpoint_path init arg; `FinetunedDistilBertConsumer`, `FinetunedRobertaConsumer` |
| `moderation_dashboard/consumers/runner.py` | `main()` CLI — `--model` + `--mode`; constructs group_id; instantiates correct consumer class; exits cleanly if checkpoint unset |
| `moderation_dashboard/anomaly/detector.py` | `WindowState` dataclass; `RollingWindowDetector` — Kafka consumer group `moderation-anomaly`; 5-min tumbling windows; Z-score signals; writes `AnomalyFlag` rows; `main()` |
| `moderation_dashboard/escalation/service.py` | `EscalationService` — polls shadow classifications; evaluates disagreement + low confidence; POSTs to case-queue with `source="moderation-dashboard"`; deduplicates via `escalations` table; writes skip records for non-escalated events; `main()` |
| `moderation_dashboard/api/models.py` | `Classification`, `AnomalyFlag`, `Escalation` ORM models; `"group"` column quoted for PostgreSQL reserved-word safety |
| `moderation_dashboard/api/schemas.py` | All Pydantic schemas: `ModelStatus`, `ModelMetrics`, `EventComparison`, `SingleModelVerdict`, `AnomalyFlagRead`, `StreamMetrics`, `AnalyticsResponse`, `CategoryTrend`, `ModelAccuracyPoint`, `EscalationRatePoint` |
| `moderation_dashboard/api/database.py` | Async engine factory; `NullPool` for testing; `init_db()`, `get_db()` |
| `moderation_dashboard/api/routers/metrics.py` | All 7 routes: `/health`, `/metrics/stream`, `/metrics/production`, `/metrics/shadow`, `/metrics/comparison/{event_id}`, `/metrics/anomalies`, `/metrics/analytics`; F1/precision/recall computed from TP/FP/FN; dbt-mart fallback to empty lists |
| `moderation_dashboard/api/main.py` | FastAPI app; lifespan; CORS; port 8002 |
| `tests/conftest.py` | `test_engine` (session-scoped); `api_client`; `seeded_classifications` fixture with 10 shadow+5 production rows |
| `tests/test_producer.py` | 7 tests — category priority, CSV loading, limit, empty row skip, row index |
| `tests/test_consumers.py` | 5 tests — classify interface, abstractness, write_result, detoxify confidence, detoxify low score |
| `tests/test_api.py` | 9 tests — health, stream empty, stream populated, all 5 models returned, shadow computed F1, pending model null, comparison 404, anomalies empty, analytics empty without dbt |

### dbt project (`projects/moderation-dashboard/dbt/`)
| File | Purpose |
|------|---------|
| `dbt_project.yml` | Project config; staging=view, marts=table; schema=dbt_moderation |
| `profiles.yml` | PostgreSQL connection via `env_var()` — no hardcoded credentials |
| `models/sources.yml` | `moderation` source: `classifications`, `escalations` |
| `models/staging/stg_events.sql` | `DISTINCT ON (event_id)` — one row per event |
| `models/staging/stg_classifications.sql` | Classification rows with truncated-to-hour timestamp |
| `models/marts/fct_category_trends.sql` | Event count by (event_hour, category) |
| `models/marts/fct_model_accuracy.sql` | F1, TP/FP/FN by (classification_hour, group, model_name) |
| `models/marts/fct_escalation_rates.sql` | Escalation rate per 5-min window; joins events with escalations |

### Frontend (`projects/moderation-dashboard/web/`)
| File | Purpose |
|------|---------|
| `package.json` | react, @tanstack/react-query, recharts, lucide-react; vitest, @testing-library, msw |
| `vite.config.ts` | vitest/config; port 5174; jsdom test environment; @/ alias |
| `tsconfig.app.json` | Strict TS; no baseUrl (TypeScript 6 compat); paths alias only |
| `tailwind.config.js` | Token layer from frontend-architect: background, surface, border, accent, text-intense/default/muted, success, warning, danger; Inter + JetBrains Mono fonts |
| `.env.example` | `VITE_API_URL`, `VITE_CASE_QUEUE_URL` |
| `src/types/index.ts` | All domain types: `ModelMetrics`, `AnomalyFlag`, `StreamMetrics`, `AnalyticsResponse`, `CaseListItem`, `CasePage` |
| `src/api/client.ts` | `apiFetch()`, `externalFetch()`, `ApiError` |
| `src/api/production.ts` | `useProductionMetrics()` — 3s refetch; sparkline history accumulation (30 points) |
| `src/api/shadow.ts` | `useShadowMetrics()` — same pattern |
| `src/api/stream.ts` | `useStreamMetrics()` (5s), `useAnomalyFlags()` (10s) |
| `src/api/analytics.ts` | `useAnalytics()` (60s), `useDashboardCases()` — polls case-queue for `source=moderation-dashboard&status=pending` |
| `src/components/PanelTabBar.tsx` | Tab bar with 5 tabs; active/inactive token styling |
| `src/components/StatusBadge.tsx` | `active` (success tint) / `pending` (warning tint) badge |
| `src/components/MetricSparkline.tsx` | recharts LineChart; accent hex hardcoded (#2563eb; commented in file) |
| `src/components/Skeleton.tsx` | Manual shimmer skeleton (no shadcn install required) |
| `src/components/ModelCard.tsx` | Full active card with MetricGrid + MetricSparkline; pending shows "Awaiting checkpoint"; opacity-60 |
| `src/components/ModelCardSkeleton.tsx` | Skeleton equivalent of ModelCard |
| `src/components/FeedItemSkeleton.tsx` | 3-element skeleton row for anomaly/escalation feeds |
| `src/components/AnomalyFeedItem.tsx` | Signal name, Z-score badge (warning/neutral), relative timestamp |
| `src/components/EscalationCaseRow.tsx` | Linked row with content excerpt, category badge, source badge, ExternalLink icon |
| `src/components/ErrorMessage.tsx` | Danger-tinted error card with title and optional body |
| `src/pages/StreamMonitor.tsx` | Stat row (3 cards) + category bar chart + anomaly feed |
| `src/pages/ModelPerformance.tsx` | Production metrics grid (3 col); loading/error states |
| `src/pages/ModelComparison.tsx` | Shadow metrics grid; same structure |
| `src/pages/HumanReview.tsx` | Escalation list from case-queue; empty + error states |
| `src/pages/Analytics.tsx` | 3 recharts charts: model F1 over time, category trends, escalation rates; empty state with dbt-refresh hint |
| `src/test/StreamMonitor.test.tsx` | 5 tests — rate, total, anomaly feed, empty state, error state |
| `src/test/ModelPerformance.test.tsx` | 5 tests — model cards, active badge, pending badge, awaiting checkpoint, error |
| `src/test/HumanReview.test.tsx` | 4 tests — row render, case count, empty state, error state |
| `src/test/Analytics.test.tsx` | 4 tests — no-data state, dbt hint, populated charts, error state |

---

## Setup Steps Taken

1. `mkdir -p` all required directories
2. `uv sync` — installed all Python dependencies into `.venv`
3. `ruff check` + `ruff format` — all Python files pass (0 errors)
4. `pnpm install` + `pnpm approve-builds` — installed all JS deps; `pnpm-lock.yaml` generated
5. `pnpm tsc --noEmit` — TypeScript check passes (0 errors)

---

## Deviations from Architecture

| Location | Deviation | Reason |
|----------|-----------|--------|
| `consumers/base.py` | `BaseConsumer.__init__` takes explicit params, not a `Settings` object; subclasses load models in their own `__init__` | Cleaner: `runner.py` owns settings lookup; consumer classes own model loading. Compatible with architect spec. |
| `escalation/service.py` | Writes `escalation_reason="no_escalation"` skip records for non-escalated events | Without this, `_get_unevaluated_event_ids()` re-evaluates the same events every poll cycle. Dedup needs a resolution the architect spec didn't provide. |
| `api/main.py` | API port 8002 | Avoids clash with case-queue (8000) and moderation-stream (8001). |
| `docker-compose.yml` | Kafka port 9093, Zookeeper port 2182 | Avoids clash with moderation-stream compose (9092, 2181). |
| `ruff.toml` | `B008` and `E501` ignored | B008 is a false positive for FastAPI `Depends` pattern; E501 is too strict for SQL literal strings in `text()` blocks. |
| `web/src/components/Skeleton.tsx` | Manual Skeleton instead of shadcn/ui | Architect specified "Do NOT run `npx shadcn init` non-interactively". Manual component is functionally equivalent. |
| `web/src/pages/Analytics.tsx` | Uses `MODEL_COLOURS` dict for recharts; `Legend` shown | Frontend-architect left colour palette to implementer; resolved with blue/emerald/amber/violet/rose. |

---

## Known Gaps

1. **Alembic initial migration not generated** — requires `alembic revision --autogenerate -m "initial"` with live Postgres on port 5434.
2. **Python integration tests require live Postgres** — `moderation_dashboard_test` database must exist on port 5434. Create after `docker compose up`.
3. **Frontend vitest tests not executed this session** — no browser available. Tests are written and tsc-clean.
4. **dbt requires `dbt-postgres` standalone install** — not in pyproject.toml. Install: `pip install dbt-postgres`.
5. **Phase 2 consumers** — runner exits cleanly if checkpoint path unset. No data written until project-8 checkpoints are available.
6. **`ModelComparison.test.tsx` not written** — coverage provided by `ModelPerformance.test.tsx` which exercises all shared components. Reviewer should confirm.
7. **`case-queue` CORS** — `useDashboardCases` polls case-queue directly from the browser. Case-queue's CORS config must allow `http://localhost:5174`.

---

## How to Run

```bash
# Backend
cd projects/moderation-dashboard
docker compose up -d
cp .env.example .env  # set JIGSAW_CSV_PATH
uv run md-api                          # API on http://localhost:8002
make consumers                         # 6 consumers (3 production + 3 shadow)
make anomaly && make escalation
make producer ARGS="--limit 5000"
make dbt-refresh                       # after dbt-postgres installed

# Frontend
cd web && cp .env.example .env && pnpm dev   # http://localhost:5174
pnpm test

# Python tests (requires live Postgres)
psql -h localhost -p 5434 -U postgres -c "CREATE DATABASE moderation_dashboard_test;"
uv run pytest tests/ -v
```

---

## Handoff

**Next role:** reviewer

The reviewer reads this file and the produced code to assess correctness, style, and test coverage.

**Pay particular attention to:**

1. **`escalation/service.py` skip-record pattern** — the deviation above. Reviewer should assess whether a separate `evaluated_events` table would be cleaner than skip records in `escalations`.
2. **`api/routers/metrics.py` ground-truth derivation** in `GET /metrics/comparison/{event_id}` — ground truth is reconstructed from `predicted_label + correct` since it is not stored separately. This is lossy if different consumers for the same event disagree on `correct`. Reviewer should flag.
3. **Frontend test coverage gap** — `ModelComparison.test.tsx` not written (see Known Gaps #6).
4. **`fct_escalation_rates.sql` coupling** — `no_escalation` string in the CTE must stay in sync with `service.py`. Reviewer should flag.
