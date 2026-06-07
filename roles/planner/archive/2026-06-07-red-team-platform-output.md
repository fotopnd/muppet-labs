# Planner Output — red-team-platform

**Role:** planner
**Sequence:** `new-project-full` (step 2)
**Date:** 2026-06-07

---

## Project

`red-team-platform` — a local automated red-team evaluation system that seeds a jailbreak corpus from `sevdeawesome/jailbreak_success`, assigns harm categories via the taxonomy classifier at seed time, fires attacks at a local Ollama model, scores responses with the pair classifier, clusters failures by semantic similarity, and visualises everything in a 6-tab React dashboard.

---

## Brief Flags Resolved

**Sevdeawesome dataset field names — open question**
The exact column names in `sevdeawesome/jailbreak_success` are unverified. Architect documents likely field names and the inspection step. Implementer runs `load_dataset('sevdeawesome/jailbreak_success', split='train[:5]')` and inspects `.features` before writing the data loader. All field name constants live in `src/corpus/constants.py`; they are the only place to update when field names differ.

**Cluster k=8 — env var**
`CLUSTER_K` env var, default 8. Configurable. Implementer reads from `Settings`.

**Port 8003**
No existing workspace service uses 8003. Confirmed.

---

## Requirements

### Corpus Seeder (`uv run seed-corpus`)

1. Load `sevdeawesome/jailbreak_success` from HuggingFace datasets (cached after first pull).
2. For each row, extract: `attack_text` (the jailbreak prompt), `strategy` (the jailbreak technique), and `harm_goal` (the underlying harmful objective text used for taxonomy classification).
3. Run the taxonomy classifier (`taxonomy-2026-06-07`) on the `harm_goal` text. Assign the top-scoring category label as `harm_category`. The taxonomy classifier is loaded once for the whole seeding pass.
4. Upsert each record into the `attacks` table using `(source, source_id)` as the upsert key. `source = "sevdeawesome"`. `source_id = f"sev-{row_index}"`.
5. Print a summary: `Seeded N attacks, skipped M (already present)`.

### Attack Runner (`uv run attack`)

6. Accept optional flags: `--source`, `--harm-category`, `--strategy`.
7. Create a `RunSession` row, iterate over filtered attacks, POST each to Ollama (`/api/chat`, stream=false), score the response with the pair classifier, write a `Run` row, close the session with aggregate stats, refresh the `coverage_summary` materialised view.
8. Log progress every 10 attacks at INFO. Log timeouts at WARNING with attack ID; skip the run row (no partial data).
9. Fail fast at startup if pair classifier path is invalid.

### Failure Clustering (`uv run cluster`)

10. Read all `runs` rows where `jailbreak_success=True` from the DB, joined to `attacks` for `attack_text`, `harm_category`, `strategy`.
11. If fewer than `CLUSTER_K` successful runs exist, exit with a clear message: `Not enough failures to cluster (need at least CLUSTER_K, have N)`.
12. Vectorise `attack_text` with sklearn `TfidfVectorizer` (max_features=5000, stop_words='english').
13. Cluster with `KMeans(n_clusters=CLUSTER_K, random_state=42)`.
14. For each cluster: find the run whose TF-IDF vector is closest to the centroid (representative), count cluster size, find the mode `harm_category` and mode `strategy` across cluster members.
15. Delete and reinsert `failure_clusters` and `cluster_summaries` rows (full overwrite — clustering is not incremental in v1).
16. Print a summary table: cluster_id, size, top_harm_category, top_strategy, representative text (first 80 chars).

### FastAPI Backend

17. `GET /coverage` — queries `coverage_summary` materialised view, returns `CoverageOut`.
18. `GET /strategy-comparison` — aggregates `runs` by strategy, returns `StrategyComparisonOut`.
19. `GET /regression` — returns all `run_sessions` ordered by `created_at` ASC, returns `RegressionOut`.
20. `GET /attacks` — paginated, filterable by source/harm_category/strategy.
21. `GET /sessions` — all sessions ordered by `created_at` DESC.
22. `GET /runs` — paginated, filterable by session_id.
23. `GET /sample/{run_id}` — single run detail for Sample Review tab.
24. `GET /clusters` — returns all `cluster_summaries`, returns `ClustersOut`.
25. `GET /clusters/{cluster_id}/members` — returns `ClusterMembersOut` (list of run + attack details for that cluster).
26. `GET /attacks/harm-categories` and `GET /attacks/strategies` — distinct filter values for dropdowns.
27. Pair classifier loaded at startup via lifespan; fails fast if path invalid. Taxonomy classifier NOT loaded at API startup (only needed by seed CLI).

### React Dashboard

28. **Tab 1 — Attack Browser**: paginated attacks table. Filter dropdowns for harm_category and strategy (populated from `/attacks/harm-categories` and `/attacks/strategies`). Source is a text input (not DB-enumerated; only one source in v1).
29. **Tab 2 — Coverage Heatmap**: recharts ScatterChart heatmap. X: harm_category. Y: strategy. Colour: ASR (green→red). Tooltip shows total_runs, total_successes, asr.
30. **Tab 3 — Strategy Comparison**: recharts BarChart, X: strategy, Y: ASR %, sorted descending.
31. **Tab 4 — Regression Tracker**: recharts LineChart, X: session date, Y: ASR %, one line per model_name.
32. **Tab 5 — Sample Review**: session dropdown → runs table → click row → full sample detail (attack text, response text, classifier score badge, latency).
33. **Tab 6 — Failure Clusters**: grid of cluster cards. Each card: cluster ID badge, size, top_harm_category chip, top_strategy chip, representative text (truncated), expandable member list (renders on click, fetches `/clusters/{id}/members`).
34. All tabs: loading skeleton, error state, empty state handled.

### Tests

35. Python: pytest-asyncio, all external calls mocked (HuggingFace via pytest-mock, Ollama via pytest-httpserver, classifiers via pytest-mock). Aggregation endpoints tested with seeded data asserting computed values.
36. TypeScript: vitest + @testing-library/react + MSW. One test file per page component. Tests assert visible content; no snapshot tests.

---

## Technology Stack

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | workspace standard |
| Package manager | uv | workspace standard |
| Formatter/linter | ruff | workspace standard |
| Web framework | FastAPI (async) | workspace standard |
| ORM | SQLAlchemy 2.x async | async sessions; Pydantic-compatible |
| DB driver | asyncpg | async Postgres |
| Migrations | Alembic | workspace standard |
| Settings | pydantic-settings, extra="ignore" | workspace convention |
| ML classifiers | transformers.pipeline | same pattern as llm-safety-monitor |
| Clustering | scikit-learn (TfidfVectorizer + KMeans) | lightweight; no GPU needed |
| Ollama client | httpx.AsyncClient | async; already in the dep graph |
| DB | PostgreSQL 16 (port 5435, DB name: redteam) | |
| Frontend language | TypeScript 5.x, strict | workspace standard |
| Frontend framework | React 18 | workspace standard |
| Package manager (FE) | pnpm | workspace standard |
| Build tool | Vite | workspace standard |
| Server state | TanStack Query | workspace standard |
| Charts | recharts | established in workspace |
| UI | shadcn/ui | workspace standard |
| Testing (Python) | pytest + pytest-asyncio + pytest-httpserver + pytest-mock | |
| Testing (TS) | vitest + @testing-library/react + MSW | workspace standard |

---

## File and Module Structure

```
projects/red-team-platform/
├── pyproject.toml
├── ruff.toml
├── .env.example
├── docker-compose.yml
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
├── src/
│   └── red_team_platform/
│       ├── __init__.py
│       ├── config.py                        ← pydantic-settings Settings
│       ├── models.py                        ← SQLAlchemy ORM: Attack, RunSession, Run, FailureCluster, ClusterSummary
│       ├── db.py                            ← async engine, session factory, get_db_session()
│       ├── corpus/
│       │   ├── __init__.py
│       │   ├── constants.py                 ← sevdeawesome field name constants
│       │   ├── loader.py                    ← load_sevdeawesome() → list[AttackRecord]
│       │   └── seed.py                      ← seed_corpus(session, records) + CLI main()
│       ├── runner/
│       │   ├── __init__.py
│       │   ├── classifier.py                ← pair classifier singleton: get_classifier(), score()
│       │   ├── taxonomy_classifier.py       ← taxonomy classifier singleton: get_taxonomy_classifier(), classify_category()
│       │   ├── ollama_client.py             ← chat(client, model, prompt) → (str, int)
│       │   └── attack.py                    ← run_session() + CLI main()
│       ├── cluster/
│       │   ├── __init__.py
│       │   └── kmeans.py                    ← cluster_failures() + CLI main()
│       └── api/
│           ├── __init__.py
│           ├── schemas.py                   ← all Pydantic response models
│           ├── deps.py                      ← get_db() FastAPI dependency
│           ├── main.py                      ← FastAPI app + lifespan
│           └── routers/
│               ├── __init__.py
│               ├── attacks.py               ← GET /attacks, /attacks/harm-categories, /attacks/strategies
│               ├── runs.py                  ← GET /runs, GET /sample/{run_id}
│               ├── sessions.py              ← GET /sessions
│               ├── coverage.py              ← GET /coverage
│               ├── strategy.py              ← GET /strategy-comparison
│               ├── regression.py            ← GET /regression
│               └── clusters.py             ← GET /clusters, GET /clusters/{cluster_id}/members
├── tests/
│   ├── conftest.py
│   ├── test_seed.py
│   ├── test_attack.py
│   ├── test_cluster.py
│   └── test_api.py
└── web/
    ├── package.json
    ├── pnpm-lock.yaml
    ├── vite.config.ts
    ├── tsconfig.json
    ├── eslint.config.ts
    ├── .env.example
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx                          ← 6-tab layout
    │   ├── types/
    │   │   └── index.ts                     ← all TypeScript domain types
    │   ├── hooks/
    │   │   ├── useAttacks.ts
    │   │   ├── useAttackFilters.ts
    │   │   ├── useSessions.ts
    │   │   ├── useRuns.ts
    │   │   ├── useSample.ts
    │   │   ├── useCoverage.ts
    │   │   ├── useStrategyComparison.ts
    │   │   ├── useRegression.ts
    │   │   ├── useClusters.ts
    │   │   └── useClusterMembers.ts
    │   └── pages/
    │       ├── AttackBrowser.tsx
    │       ├── CoverageHeatmap.tsx
    │       ├── StrategyComparison.tsx
    │       ├── RegressionTracker.tsx
    │       ├── SampleReview.tsx
    │       └── FailureClusters.tsx
    └── src/test/
        ├── setup.ts
        ├── handlers.ts                      ← MSW handlers for all API endpoints
        ├── AttackBrowser.test.tsx
        ├── CoverageHeatmap.test.tsx
        ├── StrategyComparison.test.tsx
        ├── RegressionTracker.test.tsx
        ├── SampleReview.test.tsx
        └── FailureClusters.test.tsx
```

---

## Open Questions for Architect

**OQ1 — Sevdeawesome field names.**
`sevdeawesome/jailbreak_success` has ~10,800 rows. Likely fields: `jailbreak_query` (the attack text), `strategy` (jailbreak technique), `harm_goal` or `behavior` (the harmful objective). Exact names unverified. Architect documents the inspection step and most likely names based on the dataset card; implementer confirms before writing `loader.py`. All names go in `constants.py` only.

**OQ2 — Taxonomy classifier output format.**
The taxonomy classifier (`taxonomy-2026-06-07`) was trained as a multi-label classifier. At seed time we need the single top-scoring category. Architect specifies: load with `pipeline("text-classification", top_k=1)` or `top_k=None` and take argmax? Proposed: `top_k=1` returns `[{"label": "...", "score": float}]`; take `result[0]["label"]`. Verify label strings match the 13 WildGuard category names exactly.

**OQ3 — Cluster overwrite strategy.**
`uv run cluster` is idempotent via full DELETE+INSERT on `failure_clusters` and `cluster_summaries`. This is safe because clustering is a read-only transformation over `runs` data. Architect confirms this is the right approach vs. adding a `cluster_run_id` versioning column (proposed: full overwrite in v1, versioning is v2).

**OQ4 — `coverage_summary` refresh.**
Confirm plain `REFRESH MATERIALIZED VIEW` (not CONCURRENTLY) in v1, consistent with the earlier architect decision.

**OQ5 — Backend port.**
Port 8003 (confirmed free). Architect locks this in `.env.example`.

---

## Handoff

**Next role:** architect

The architect reads this file and the brief to define: all SQLAlchemy ORM models (including `FailureCluster` and `ClusterSummary`), all Pydantic schemas for the clusters endpoints, all module interfaces for `taxonomy_classifier.py` and `cluster/kmeans.py`, DB migration SQL, frontend types and hooks for the Failure Clusters tab, and the `FailureClusters.tsx` component spec. The existing red-team-platform architect output (`roles/architect/archive/2026-06-06-red-team-platform-output.md`) is the base — architect extends it with the new corpus, taxonomy, and clustering additions. Do not re-derive what is already settled.
