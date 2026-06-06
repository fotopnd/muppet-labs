# Planner Output — red-team-platform

**Role:** planner
**Sequence:** `new-project-full` (step 2)
**Date:** 2026-06-06

---

## Project

`red-team-platform` — a local offensive safety evaluation platform that replays JailbreakBench and AdvBench adversarial attack corpora against a local Ollama LLM, scores responses with a shared DistilBERT pair-classifier checkpoint, and surfaces coverage and regression metrics via a 5-tab React dashboard.

---

## Brief Flags Resolved

**Flag: dataset field names may vary**
Decision: all HuggingFace field names are defined as module-level constants in `src/corpus/constants.py`. Loader functions reference these constants, not string literals. If the upstream schema changes, one file changes.

**Flag: strategy field missing**
Decision: if a JailbreakBench item has no strategy tag, the loader assigns `strategy = "unknown"` and emits a `logger.warning`. This is safe because the coverage heatmap groups by strategy — unknown is a valid bin.

**Flag: multi-session run tracking**
Decision: the `run_sessions` table stores one row per attack session (model version, timestamp, total attacks, total successes). The `runs` table has a `session_id` FK. The Regression Tracker endpoint queries `run_sessions` ordered by `created_at` and returns per-session ASR.

**Flag: coverage_summary refresh**
Decision: the materialised view is refreshed via `REFRESH MATERIALIZED VIEW CONCURRENTLY coverage_summary` at the end of each run session, called by the runner after the last row is committed. Not triggered per-row — too expensive.

---

## Requirements

1. `uv run seed-corpus` loads JailbreakBench (`JailbreakBench/JailbreakBench`) and AdvBench (`llm-attacks/advbench`) from HuggingFace and upserts rows into the `attacks` table. Re-running the command is idempotent (upsert on `(source, source_id)`).
2. Each `attacks` row has: `id` (UUID), `source` (`jailbreakbench` | `advbench`), `source_id` (string, original dataset key), `harm_category` (string), `strategy` (string, `"direct"` or `"unknown"` if untagged), `attack_text` (text), `created_at` (timestamptz).
3. `uv run attack` creates a `run_sessions` row, iterates over a filtered subset of `attacks` (filterable by `--source`, `--harm-category`, `--strategy`), sends each to Ollama `/api/chat`, scores the response with `pair_classifier`, and writes a `runs` row per attack. Default: all attacks.
4. Each `runs` row has: `id` (UUID), `session_id` (FK → `run_sessions`), `attack_id` (FK → `attacks`), `model_name` (string, from `OLLAMA_MODEL`), `response_text` (text), `jailbreak_success` (bool), `classifier_score` (float, the unsafe class probability), `latency_ms` (int), `created_at` (timestamptz).
5. The `run_sessions` table has: `id` (UUID), `model_name` (string), `total_attacks` (int), `total_successes` (int), `asr` (float, computed column or written on close), `created_at` (timestamptz).
6. A `coverage_summary` materialised view aggregates `jailbreak_success` rates grouped by `harm_category × strategy` across all runs (latest session by default; architect decides on session scoping).
7. FastAPI exposes: `GET /attacks` (paginated, filterable), `GET /runs` (paginated by session), `GET /sessions` (list of run_sessions), `GET /coverage` (heatmap data), `GET /strategy-comparison` (bar chart data), `GET /regression` (line chart data), `GET /sample/{run_id}` (full prompt + response).
8. The React dashboard has exactly five tabs: Attack Browser, Coverage Heatmap, Strategy Comparison, Regression Tracker, Sample Review. Each tab is a separate page component with its own TanStack Query hook.
9. The Coverage Heatmap tab renders a recharts `ScatterChart` used as a heatmap (colour-encoded by ASR value) with `harm_category` on the X axis and `strategy` on the Y axis.
10. The Regression Tracker tab renders a recharts `LineChart` with one line per unique `model_name`, X axis = session timestamp, Y axis = ASR.
11. The `PAIR_CLASSIFIER_PATH` env var must be set and must point to a valid directory containing `config.json`. The runner raises `RuntimeError` with a descriptive message if the path is missing or invalid — not a silent default.
12. All filter dropdowns in the Attack Browser are populated from `GET /attacks/harm-categories` and `GET /attacks/strategies` endpoints returning `string[]` — not hardcoded in the frontend.
13. pytest test suite achieves coverage of: corpus loader (mocked datasets), attack runner (mocked httpx to Ollama), classifier scoring (mocked transformers pipeline), all seven API endpoints (seeded DB).
14. vitest test suite covers all five dashboard tabs with MSW-mocked API responses.

---

## Technology Stack

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | Workspace standard; HuggingFace ecosystem |
| Package manager | uv | Workspace standard |
| Formatter / linter | ruff | Workspace standard |
| Web framework | FastAPI 0.111 | Async, typed, OpenAPI docs — matches llm-safety-monitor |
| ORM | SQLAlchemy 2.x (async) | Consistent with llm-safety-monitor; typed models |
| DB migrations | Alembic | SQLAlchemy companion; idempotent migration history |
| HTTP client (runner) | httpx (async) | Native async; used for Ollama calls |
| HuggingFace datasets | `datasets` library | Standard; cache-aware; offline-capable after first pull |
| Classifier inference | `transformers` pipeline | `pair_classifier` checkpoint is HF-format |
| Testing | pytest + pytest-asyncio | Workspace standard |
| Frontend language | TypeScript 5.x | Workspace standard |
| Frontend build | Vite | Fast HMR; standard for React + TS |
| Package manager (FE) | pnpm | Workspace standard |
| State / data fetching | TanStack Query v5 | Server state; refetch intervals for live data |
| Charts | recharts 2.x | `ScatterChart` for heatmap; `LineChart` for regression |
| UI components | shadcn/ui | Consistent component library |
| Testing (FE) | vitest + MSW | Workspace standard; mock at network boundary |
| Database | PostgreSQL 16 | Port 5435 |

---

## File and Module Structure

```
projects/red-team-platform/
├── pyproject.toml               ← uv project; [tool.uv.scripts] for seed-corpus, attack
├── .env.example
├── alembic.ini
├── alembic/
│   └── versions/
│       └── 001_initial_schema.py
├── src/
│   ├── config.py                ← pydantic-settings Settings; reads .env; extra="ignore"
│   ├── db.py                    ← async SQLAlchemy engine + session factory
│   ├── models.py                ← SQLAlchemy ORM: Attack, RunSession, Run
│   ├── corpus/
│   │   ├── __init__.py
│   │   ├── constants.py         ← HF dataset field name constants
│   │   ├── loader.py            ← load_jailbreakbench(), load_advbench() → list[AttackRecord]
│   │   └── seed.py              ← CLI entry point: uv run seed-corpus
│   ├── runner/
│   │   ├── __init__.py
│   │   ├── ollama_client.py     ← async Ollama /api/chat wrapper
│   │   ├── classifier.py        ← pair_classifier inference wrapper
│   │   └── attack.py            ← CLI entry point: uv run attack
│   └── api/
│       ├── __init__.py
│       ├── main.py              ← FastAPI app factory; mounts routers
│       ├── deps.py              ← async DB session dependency
│       ├── schemas.py           ← Pydantic response models (all API shapes)
│       └── routers/
│           ├── attacks.py       ← GET /attacks, /attacks/harm-categories, /attacks/strategies
│           ├── runs.py          ← GET /runs, /sample/{run_id}
│           ├── sessions.py      ← GET /sessions
│           ├── coverage.py      ← GET /coverage
│           ├── strategy.py      ← GET /strategy-comparison
│           └── regression.py    ← GET /regression
├── tests/
│   ├── conftest.py              ← async DB fixture, seeded test data
│   ├── test_corpus_loader.py
│   ├── test_runner.py
│   ├── test_classifier.py
│   └── test_api/
│       ├── test_attacks.py
│       ├── test_runs.py
│       ├── test_sessions.py
│       ├── test_coverage.py
│       ├── test_strategy.py
│       └── test_regression.py
└── web/
    ├── package.json
    ├── pnpm-lock.yaml
    ├── vite.config.ts
    ├── tsconfig.json
    ├── .env.example
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx              ← tab router (5 tabs)
    │   ├── api/
    │   │   └── client.ts        ← axios base instance; VITE_API_URL
    │   ├── hooks/
    │   │   ├── useAttacks.ts
    │   │   ├── useAttackFilters.ts   ← harm-categories + strategies dropdowns
    │   │   ├── useRuns.ts
    │   │   ├── useSessions.ts
    │   │   ├── useCoverage.ts
    │   │   ├── useStrategyComparison.ts
    │   │   ├── useRegression.ts
    │   │   └── useSample.ts
    │   ├── types/
    │   │   └── index.ts         ← TypeScript types mirroring Pydantic schemas
    │   └── pages/
    │       ├── AttackBrowser.tsx
    │       ├── CoverageHeatmap.tsx
    │       ├── StrategyComparison.tsx
    │       ├── RegressionTracker.tsx
    │       └── SampleReview.tsx
    └── src/test/
        ├── setup.ts             ← MSW server setup
        ├── handlers.ts          ← MSW route handlers
        ├── AttackBrowser.test.tsx
        ├── CoverageHeatmap.test.tsx
        ├── StrategyComparison.test.tsx
        ├── RegressionTracker.test.tsx
        └── SampleReview.test.tsx
```

---

## Open Questions for Architect

1. **coverage_summary session scoping.** The brief says "latest session by default" — but the heatmap is most useful aggregated across all sessions (more attack coverage). Proposed answer: aggregate across all runs, not scoped to a single session. The Session filter can be added in v2. Architect confirms.

2. **Ollama request timeout.** Local models can be slow. Proposed answer: `httpx` timeout of 120s per request; configurable via `OLLAMA_TIMEOUT_S` env var. Architect confirms or adjusts.

3. **pair_classifier loading strategy.** Load once at startup (module-level singleton) or per-request lazy load. Proposed answer: load once at FastAPI startup using `@app.on_event("startup")` — raises `RuntimeError` if path invalid, so the server never starts in a broken state. Attack runner also loads it once per session. Architect confirms.

4. **`coverage_summary` UNIQUE index.** The materialised view needs a unique index for `CONCURRENTLY` refresh. Proposed answer: `CREATE UNIQUE INDEX ON coverage_summary (harm_category, strategy)`. Architect to confirm this is included in the migration.

---

## Handoff

**Next role:** architect

The architect reads this output and the brief to produce the full implementer-ready design: complete ORM models, Pydantic schemas for every API endpoint, all function signatures, the DB migration SQL, the materialised view SQL, TypeScript types and hooks, and resolution of the four open questions above.

**Flags for architect:**
- Open question 1 (coverage_summary scoping) is the most ambiguous — confirm before writing the view SQL, as the SQL changes materially depending on the answer.
- Open question 3 (classifier loading) affects both the FastAPI startup lifecycle and the runner CLI — the two load sites should use the same singleton pattern.
- The `ScatterChart`-as-heatmap pattern in recharts is non-obvious — implementer will need explicit guidance on how to encode ASR as fill colour (use `Cell` with a colour scale function).
- The `run_sessions.asr` column: decide whether it is a stored computed column written at session close or a generated column. Stored (written by the runner) is simpler and avoids Postgres generated column constraints.
