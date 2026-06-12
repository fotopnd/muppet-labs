# Implementer Output — red-team-platform

**Role:** implementer
**Sequence:** `new-project-full` (step 4)
**Date:** 2026-06-07
**Project:** `projects/red-team-platform/`

---

## What Was Built

Full project scaffold delivered per architect spec (2026-06-06 + 2026-06-07 outputs).

### Python Backend (`src/red_team_platform/`)

| File | Status |
|------|--------|
| `config.py` | Done — 9 Settings fields incl. sync_database_url, taxonomy_classifier_path, cluster_k |
| `models.py` | Done — 5 ORM classes: Attack, RunSession, Run, FailureCluster, ClusterSummary |
| `db.py` | Done — async engine + session factory helpers |
| `corpus/constants.py` | Done — sevdeawesome field constants |
| `corpus/loader.py` | Done — `load_sevdeawesome()`, skips malformed rows, harm_goal set |
| `corpus/seed.py` | Done — taxonomy classifier called per record, upsert on conflict |
| `runner/taxonomy_classifier.py` | Done — singleton pipeline, `classify_category()` |
| `runner/classifier.py` | Done — pair classifier singleton, `score()` |
| `runner/ollama_client.py` | Done — POSTs to `/api/chat`, `make_client()` |
| `runner/attack.py` | Done — `run_session()` async, typer CLI |
| `cluster/kmeans.py` | Done — `cluster_failures()` pure TF-IDF+KMeans, `main()` sync DB |
| `api/schemas.py` | Done — all schemas incl. cluster types |
| `api/routers/` | Done — 7 routers (attacks, runs, sessions, coverage, strategy, regression, clusters) |
| `api/main.py` | Done — lifespan loads classifier, CORS, 7 routers registered |
| `alembic/versions/001_initial_schema.py` | Done — all 5 tables + coverage_summary view |

### TypeScript Frontend (`web/`)

| File | Status |
|------|--------|
| `src/types/index.ts` | Done — all 16 types incl. cluster types |
| `src/hooks/` | Done — 9 hooks (useAttacks, useAttackFilters, useSessions, useRuns, useCoverage, useStrategyComparison, useRegression, useSample, useClusters) |
| `src/pages/AttackBrowser.tsx` | Done |
| `src/pages/CoverageHeatmap.tsx` | Done — ScatterChart heatmap with ASR colour scale |
| `src/pages/StrategyComparison.tsx` | Done — BarChart sorted by ASR |
| `src/pages/RegressionTracker.tsx` | Done — LineChart per model |
| `src/pages/SampleReview.tsx` | Done — session dropdown, run table, full sample panel |
| `src/pages/FailureClusters.tsx` | Done — cluster cards + expandable members table |
| `src/App.tsx` | Done — QueryClientProvider + 6-tab nav |
| `src/test/handlers.ts` | Done — MSW handlers for all 11 API endpoints |
| `src/test/App.test.tsx` | Done — tab bar render test, passes |

### Infra / Config

| File | Status |
|------|--------|
| `docker-compose.yml` | Done — postgres:16 on port 5435 |
| `pyproject.toml` | Done — 4 CLI scripts, pytest config |
| `ruff.toml` | Done |
| `.env.example` (backend) | Done |
| `web/.env.example` | Done |
| `benchmarks/results.md` | Done — stub |

---

## Build Verification

- `uv run ruff check . && uv run ruff format --check .` — **0 errors**
- `pnpm build` in `web/` — **0 TypeScript errors, builds to dist/**
- `pnpm test` in `web/` — **1/1 passed**

---

## Known Limitations

- Python pytest suite requires a live PostgreSQL DB at port 5435. Not run in this session.
- Frontend uses plain inline styles (no Tailwind/shadcn — interactive `shadcn init` cannot run in non-TTY).
- `web/` bundle is ~613 kB (recharts is large) — acceptable for local dev tool.

---

## Handoff

**Next step for the human:**

```bash
# Start postgres
docker compose up -d

# Run migrations
cd projects/red-team-platform && uv run alembic upgrade head

# Seed corpus (requires taxonomy model + HuggingFace download)
uv run seed-corpus

# Start API
uv run api

# Start frontend dev server
cd web && pnpm dev
```

The platform is ready for a first attack session once Ollama is running with `qwen2.5-coder:7b`.
