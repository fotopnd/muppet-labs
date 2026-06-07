# Brief Output — red-team-platform

**Role:** brief
**Sequence:** `new-project-full` (step 1)
**Date:** 2026-06-07

---

## Project Name

`red-team-platform`

---

## Description

A local automated red-team evaluation system that fires jailbreak attack prompts at a local Ollama model (qwen2.5-coder:7b), scores responses with a fine-tuned pair classifier, and surfaces results in a 6-tab React dashboard. The corpus is seeded from `sevdeawesome/jailbreak_success` (35 jailbreak strategies × 300 harm goals); harm categories are assigned at seed time by the trained taxonomy classifier. A failure clustering step auto-groups successful jailbreaks by semantic similarity and produces a visual "weakness map" showing where the monitor breaks down systematically.

---

## Language(s)

- **Primary:** Python (corpus seeder, attack runner, clustering CLI, FastAPI backend)
- **Frontend:** TypeScript (React SPA)
- **Tooling:** uv, ruff, pnpm, prettier, eslint

Single Python project at `projects/red-team-platform/`. React SPA at `projects/red-team-platform/web/`.

---

## Success Criteria

The project is done when all of the following are true:

1. **Corpus seeded** — `uv run seed-corpus` ingests `sevdeawesome/jailbreak_success` from HuggingFace, assigns `harm_category` to each attack by running the taxonomy classifier on the harm goal text, and upserts into the `attacks` table. Idempotent (re-running is safe).

2. **Attack runner** — `uv run attack` fires each attack prompt at Ollama (qwen2.5-coder:7b), scores the response with the pair classifier, writes one `runs` row per attempt, and refreshes the `coverage_summary` materialised view on session close. Optional `--source`, `--harm-category`, `--strategy` filters.

3. **Failure clustering** — `uv run cluster` reads all `jailbreak_success=True` runs from the DB, vectorises attack texts with TF-IDF, clusters with K-means (k=8 default, configurable via `CLUSTER_K` env var), writes cluster assignments to `failure_clusters` and summaries to `cluster_summaries`. Idempotent (overwrites existing cluster data for the same run of the command).

4. **FastAPI backend** — six endpoints: `/coverage`, `/strategy-comparison`, `/regression`, `/attacks`, `/sessions`, `/clusters` (summaries + members). Pair classifier loaded at startup; fails fast if path invalid.

5. **Dashboard** — 6-tab React SPA: Attack Browser, Coverage Heatmap, Strategy Comparison, Regression Tracker, Sample Review, Failure Clusters. Failure Clusters tab shows cluster summary cards with representative text, top category/strategy, cluster size, and an expandable members list.

6. **Empirical benchmark report** — `benchmarks/results.md` with metrics table: attack success rate by strategy, by category, top 3 failure clusters, and timing (p50 latency_ms). This is the artifact that makes the portfolio piece credible, not just the code.

7. **Tests** — pytest suite (mocked HuggingFace, mocked Ollama, mocked classifier); vitest suite (MSW-mocked API responses). All tests pass.

8. **Runs locally** — Docker Compose brings up Postgres on port 5435. Backend on port 8003. Frontend on 5173.

---

## Constraints

- **Classifiers are read-only.** `resources/models/llm-safety-monitor/pair-2026-06-07` and `resources/models/llm-safety-monitor/taxonomy-2026-06-07` are loaded as-is. No training occurs in this project.
- **Ollama local only.** qwen2.5-coder:7b at `http://localhost:11434`. No cloud model calls.
- **Postgres port 5435** — shared convention with llm-safety-monitor; use DB name `redteam` to avoid collision.
- **No real-time streaming.** Dashboard polls; no WebSocket.
- **Cluster computation is a CLI step**, not triggered automatically by the attack runner. Human runs `uv run cluster` after one or more attack sessions.

---

## Out of Scope

- Multi-model comparison (single Ollama model per run; regression chart shows history across runs)
- Automated jailbreak generation (corpus is static; no LLM-generated attack augmentation in v1)
- Authentication on the API
- Cloud deployment
- AdvBench or JailbreakBench (both unavailable on Hub; sevdeawesome is the replacement)

---

## Handoff

**Next role:** planner

The planner reads this file to define functional requirements, confirm the tech stack, map the full file/module structure, and raise any open questions for the architect.

**Flags for planner:**
- The sevdeawesome dataset field names are unverified — planner should note this as an open question for the architect; the implementer must inspect before writing the data loader.
- Cluster k=8 is a default. Planner should decide whether this is hardcoded or an env var (proposed: env var `CLUSTER_K`, default 8).
- Port 8003 for the backend — confirm no existing workspace service uses this port.
