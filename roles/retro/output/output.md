# Retro — red-team-platform

**Role:** retro
**Sequence:** `new-project-full`
**Date:** 2026-06-07

---

## Project

**Name:** red-team-platform
**Sequence:** new-project-full
**Sessions:** 3 fragments (context-compacted twice)
**Roles that ran:** brief → planner → architect (2026-06-06) → architect-delta (2026-06-07) → implementer → ruff-fix → reviewer (pass 1) → implementer-fixes → reviewer (pass 2) → retro
**Outcome:** PASS WITH NOTES → fixes applied → PASS WITH NOTES

---

## What Went Well

**1 — Corpus fallback was pre-decided, zero implementer friction**

When JailbreakBench and AdvBench were unavailable on HuggingFace Hub, the switch to `sevdeawesome/jailbreak_success` was already in the Decisions Log before the implementer ran. The implementer had the field names, the dataset path, and the strategy for mapping `behavior` → `harm_category` all in the architect spec. No recovery work in the implementer pass. Pre-planning the fallback corpus in the architect session paid off immediately.

**2 — Sync/async engine separation in cluster CLI was cleanly executed**

The architect spec explicitly chose sync SQLAlchemy (psycopg2) for the cluster CLI and async (asyncpg) for the FastAPI routes. The implementer followed this without deviation. No event loop errors, no `asyncio.run()` workarounds. The convention from the moderation-stream retro ("consumers sync, API async, separate engines") transferred correctly to a new context (cluster CLI vs API) without being re-litigated.

**3 — Two-pass review caught B1 before a live DB run**

`func.avg(Run.jailbreak_success.cast(type_=None))` produces `avg(boolean)` — invalid PostgreSQL SQL, but it compiles fine in Python and passes type checking. Without a live test DB, the only checkpoint where this could be caught was the reviewer. The two-pass review sequence with a blocking B-tier finding resolved in a single implementer fix pass is working as intended.

**4 — Ruff pre-pass before handoff eliminated style noise from the review**

The implementer ran `ruff check --fix` + manual fixes for 4 non-auto-fixable issues before writing the implementer output. The reviewer found zero style issues. This means the review context was spent entirely on correctness and tests, not formatting. The vibecoding-style rule ("run linter before handoff") is holding.

**5 — Previous retro recommendations were load-bearing this session**

The SQLAlchemy engine lifecycle note (from llm-safety-monitor retro) prevented any `create_engine`-per-call pattern in the cluster CLI or API. The API Aggregation Endpoints note caused the reviewer to look specifically for SQL-level aggregation correctness — which is what caught B1. Retro findings are compounding correctly.

---

## What Could Have Gone Better

**1 — B1: `avg(boolean)` not ruled out by any convention or architect spec**

The architect spec for `StrategyComparisonOut` defined `asr: float` but gave no guidance on how to compute it in SQL. The implementer reached for `func.avg(boolean_col)` which is a natural SQLAlchemy expression — but invalid PostgreSQL SQL. No convention covered this. The fix (integer aggregates in SQL, Python-side division) is simple and should be a rule. Root cause: the aggregation convention only covers filtering and COUNT — it says nothing about which aggregate functions are valid for which column types.

**2 — Architect "delta" output pattern doubled the implementer's reading load**

The 2026-06-07 architect output was structured as "changes from 2026-06-06" — a diff, not a complete spec. The implementer had to load the 2026-06-06 file (~1000 lines) plus the 2026-06-07 delta (~200 lines) and mentally merge them. Across context compaction boundaries, this pattern risks the implementer missing content from either file. The correct pattern: the architect always produces a single consolidated output before handing off. Diffs belong in the architect's working notes, not in the file the implementer reads.

**3 — Implementer context split at language boundary (Python/TypeScript)**

The Python backend consumed enough context that the session was compacted mid-implementation. The resumed session had to fix 11 ruff errors as its first act, then build the frontend from scratch with limited context. This is the same pattern observed in the moderation-dashboard session. A full-stack project (Python backend + TypeScript frontend) consistently exceeds one implementer context window. The routing sequence has no mechanism to make this split explicit — it happens at context limits, uncontrolled.

**4 — Frontend design roles skipped — no design system**

`new-project-full` includes conditional `design-brief` and `frontend-architect` roles for projects with frontends. Both were skipped; the implementer built the frontend directly from the backend architect's spec. Result: plain inline styles, no design system, recharts default colours. Acceptable for a local dev tool, but would not survive a portfolio presentation as-is. The routing.md conditional is not enforced — there is no prompt to the human to choose whether to run `frontend-architect` for a given project.

**5 — pnpm v11 `allowBuilds` required multiple attempts to discover**

The setting moved from `package.json`'s `pnpm` field to `pnpm-workspace.yaml` in pnpm v11. This discovery took three attempts in the implementer pass. It is now recorded in the project memory file and in the Decisions Log, but not in `skills/setup-ts-pnpm.md` — the canonical reference for TypeScript project setup. Future sessions starting from the skill file will hit the same issue.

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| Implementer | Loaded 2026-06-06 architect output (~1000 lines) + 2026-06-07 delta as separate files | Medium | Architect consolidates into one complete output file before handing off. Implementer reads one file. |
| Implementer (resumed) | Ruff fix pass (11 errors) as first act of the resumed session | Low | Accept: unavoidable given context compaction. Make explicit in routing as a known backend→frontend seam. |
| Reviewer pass 1 | Loaded full code manifest to find B1 | Low | Implementer Handoff should name specific files the reviewer should prioritise. This one already named aggregation endpoints explicitly — it worked. Pattern is correct. |

### Redundancy Patterns

- The 2026-06-06 architect output and 2026-06-07 delta were both in `roles/architect/archive/`. The implementer read both. These are now stable archived references, but the pattern of shipping a delta instead of a consolidated spec created a merge obligation for the implementer. Future architect passes should consolidate before archiving.

- `db.py` exports `get_db_session` and `init_db` — neither is used outside the file. The implementer wrote them anticipating future use, which is exactly what vibecoding-style says not to do. They add noise to every context window that loads `db.py`.

### Scoping Recommendations

- Add a note to `new-project-full` in routing.md: for projects with both a Python backend and TypeScript frontend, expect the implementer to span two context windows. The backend→frontend seam should be a named checkpoint: human confirms backend is complete (ruff clean + migrations run) before the implementer starts the frontend.

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `resources/python-conventions.md` | Add to **API Aggregation Endpoints** section: "PostgreSQL does not support `avg(boolean)`. To compute a ratio from a boolean column: use `func.sum(case((col == True, 1), else_=0)).label('successes')` and `func.count().label('total')` in SQL (both valid integer aggregates), then compute `successes / total` in Python. Do not use `func.avg(boolean_col)` — it raises a PostgreSQL type error at runtime." | Directly caused B1 in this project. Most likely recurrence pattern: any endpoint that tracks a success/failure boolean and needs to compute a rate. | No |
| `skills/setup-ts-pnpm.md` | Add a subsection on pnpm v11: "In pnpm v11, build allowlists for specific packages moved out of `package.json`. The equivalent of `onlyBuiltDependencies: [msw]` is `allowBuilds:\n  msw: true` in `pnpm-workspace.yaml` (root of the workspace). The `pnpm.onlyBuiltDependencies` key in `package.json` is silently ignored in v11." | Took three implementer attempts to discover. setup-ts-pnpm.md is loaded at project init — this note prevents the issue entirely. | No |

### Skills to Update

*(None beyond the above — no new skill files needed.)*

### Routing Changes

| Sequence | Change | Reason | Human decision required? |
|----------|--------|--------|--------------------------|
| `new-project-full` | Add a note to the **architect** step: "If this is a delta architect pass (extending a prior output), consolidate the prior output and the delta into a single complete spec in `roles/architect/output/output.md` before writing to archive. The implementer reads one file, not a diff + base." | Prevents double-load pattern from repeating on any project with multiple architect passes. | No |
| `new-project-full` | Add a named seam between implementer (backend) and implementer (frontend) for full-stack projects: "For projects with both Python and TypeScript, treat the implementer as two sequential phases. After the Python backend: verify ruff clean + alembic migrations generate without error. Human confirms before TypeScript phase begins." | Makes the context-limit split explicit rather than accidental. Prevents losing backend state when the session compacts mid-implementation. | Yes — requires routing.md restructure to add the conditional |

### New Resources or Skills Needed

None. All findings map to additions in existing files.

---

## One Change to Make Now

**Add the `avg(boolean)` rule to `resources/python-conventions.md` under `## API Aggregation Endpoints`.**

Specific insertion — after the existing bullet on `total`/`count` fields:

```
- **PostgreSQL does not support `avg(boolean)`**. To compute a success rate from a boolean column:
  use `func.sum(case((col == True, 1), else_=0)).label("successes")` and `func.count().label("total")`
  (both valid integer aggregates in SQL), then divide in Python: `successes / total if total > 0 else 0.0`.
  Do not use `func.avg(boolean_col)` — it raises a PostgreSQL type error at runtime, not at query-build time.
```

This is the highest-value change because: it directly caused the only blocking issue (B1) in this project; the pattern (tracking a boolean `jailbreak_success` or `is_harmful` column and computing a rate) will recur in every safety/moderation project in this workspace; and the fix is a concrete two-line substitute, not a vague warning.

---

## Handoff

Human reviews recommendations above. Recommended actions before the next project starts:

1. **Apply now (no decision required):**
   - Add `avg(boolean)` rule to `resources/python-conventions.md` → `## API Aggregation Endpoints`
   - Add pnpm v11 `allowBuilds` note to `skills/setup-ts-pnpm.md`
   - Add architect consolidation note to `resources/routing.md` → `new-project-full` architect step

2. **Requires human decision:**
   - Add explicit backend→frontend seam to `new-project-full` routing (requires restructure)

3. Update `_config/project-state.md` to record retro complete.
