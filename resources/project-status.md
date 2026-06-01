# project-status.md — Muppet Labs Portfolio Tracker

> Tracks delivered state vs. proposal and open next steps for each project.
> Updated after each review session. Newest review date shown per project.

---

## Project 21 — Case Queue and Content Review Tool

**Last reviewed:** 2026-06-01
**Location:** `projects/case-queue/`
**Proposal target:** Software Engineer, Safeguards Foundations
**Stack:** React/TypeScript, FastAPI, PostgreSQL, Docker

### Proposal vs. Delivered

| Proposal item | Status | Notes |
|---|---|---|
| Paginated case queue (filter by category, severity, date) | ✓ | Full filter/sort, page params |
| Case detail view with structured decision form | ✓ | Approve/reject/escalate |
| Role-based action controls | ✓ | `reviewer` / `senior_reviewer` enforced |
| Audit log with actor and timestamp | ✓ | Filterable by actor, action, date |
| React/TypeScript frontend | ✓ | Vite, React Query, Tailwind CSS |
| FastAPI backend | ✓ | 3 routers, Pydantic v2 schemas |
| PostgreSQL schema with Alembic migrations | ✓ | `715088b8a08a` at head |
| Synthetic seed data (Jigsaw/LANL patterns) | ~ | `scripts/seed.py` exists, 540 cases — content quality unverified |
| `POST /cases` ingestion endpoint | ✓ | Added beyond proposal scope |
| `ai_reviewer` CLI | ✓ | Above and beyond — LLM-powered moderation automation |
| Backend tests | ✓ | 22/22 passing |
| Frontend tests | ✓ | 11/11 passing |
| shadcn/ui | ✗ | Replaced with raw Tailwind (interactive CLI not available) |
| Public README / portfolio write-up | ✗ | No narrative for a recruiter landing on the repo |
| Deployed live URL | ✗ | Not deployed |

### Next Steps

**Priority 1 — `write-doc` sequence (blocking for portfolio)**
Portfolio README targeting an Anthropic SWE recruiter. Must cover: what it is, why the architecture choices matter for trust & safety, what the `ai_reviewer` CLI demonstrates, and how to run it. This is the unlock — the code is good but completely silent on intent.

**Priority 2 — Verify seed data quality**
Open `scripts/seed.py`, check whether case content and category distribution reflects realistic Jigsaw-style moderation content. If generic, improve the generator — 30 minutes of work that changes the demo from toy to credible workload.

**Priority 3 — Deploy**
API on Fly.io or Railway (free tier), frontend on Vercel. One afternoon. The `ai_reviewer` CLI pointing at a live URL is the strongest demo path. Turns a local project into a reviewable artefact.

**Priority 4 — Highlight `ai_reviewer` prominently**
This is the differentiator — above and beyond the proposal, directly speaks to the Safeguards Foundations role. Should be front and centre in the README and the eventual one-pager, not buried in a subdirectory.

**Priority 5 — shadcn/ui (optional)**
Nice-to-have for visual polish; not a blocker for the SWE eval.

---

## Project 2 — Model Behaviour Evaluation Harness

**Last reviewed:** 2026-06-01
**Location:** `projects/eval-harness/`
**Proposal target:** Both (SWE and DE Safeguards)
**Stack:** Python, SQLite, Typer CLI, Rich

### Proposal vs. Delivered

| Proposal item | Status | Notes |
|---|---|---|
| Configurable test suite against local Qwen model (Ollama) | ✓ | `local` and `mlx` backends, OpenAI-compatible |
| Claude API backend | ✓ | `claude` backend via `anthropic` SDK |
| Logs responses to structured storage | ✓ | SQLite with full result schema |
| Scores against defined rubrics | ✓ | Heuristic + LLM-as-judge, weighted aggregate |
| Tracks metric drift across runs | ✓ | `eval diff` with per-rubric and per-dataset deltas, flip detection |
| CLI: add new test cases | ✓ | `eval add-case --prompt` or `--file` |
| CLI: run evals | ✓ | `eval run` with progress bar, run summary |
| CLI: diff results between runs | ✓ | `eval diff [run_a] [run_b]` |
| TruthfulQA integration | ✓ | HuggingFace load with CSV fallback |
| AdvBench integration | ✓ | HuggingFace load with GitHub CSV fallback |
| Unit tests | ✓ | 45 tests across scorer, drift, DB, datasets, runner |
| Portfolio one-pager (`docs/one-pager.md`) | ✓ | Full narrative document exists |
| Public README | ✓ | Setup, config, full command reference |
| Deployed / publicly accessible | ✗ | CLI tool — not deployable in the same sense; GitHub repo is the artefact |
| Dashboard / visualisation layer | ✗ | Not in proposal; `eval list` and `eval diff` are CLI-only |

### Next Steps

**Priority 1 — Publish to GitHub**
The repo is local only. The portfolio artefact for a CLI tool is a public GitHub repository with a clean README and a working `pip install` / `uv add` path. Without this, no reviewer can engage with it. This is the equivalent blocker to case-queue's missing deployment.

**Priority 2 — Run against a real model and commit results**
The `eval_results.db` exists in the repo but its content is unknown. Running `eval run` against Qwen3-Coder or Claude Sonnet on AdvBench and committing the results (or a sample thereof) would let a reviewer see the tool actually working. A `runs/` folder with a JSON export from `eval diff` would be compelling.

**Priority 3 — Add a third-party dataset or custom safety suite**
The proposal mentions building on public safety benchmarks. TruthfulQA and AdvBench are covered. Adding a small hand-authored custom YAML suite (`test_cases/`) with trust & safety specific cases (misinformation, harmful content, policy adherence) would demonstrate domain knowledge beyond benchmark plumbing.

**Priority 4 — Consider a minimal web view (optional)**
A simple `eval serve` command that renders run history and drift reports in a browser would lift this from "CLI tool" to "dashboard" and close the visualisation gap. Not in the original proposal, but would differentiate strongly. Worth one `add-feature` sequence if the higher-priority items are done.

---

## Status Summary

| # | Project | Code complete | Tests | Docs | Deployed/Published | Priority gap |
|---|---|---|---|---|---|---|
| 21 | Case Queue | ✓ | ✓ | ✗ | ✗ | write-doc + deploy |
| 2 | Eval Harness | ✓ | ✓ | ✓ | ✗ | GitHub publish + commit results |
