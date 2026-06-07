# Reviewer Output — red-team-platform (pass 2)

**Role:** reviewer
**Sequence:** new-project-full (step 5, second pass)
**Date:** 2026-06-07
**Context:** Re-review after implementer resolved B1, W2, T1 from pass 1.

---

## Summary

All three blocking/required items from pass 1 are resolved. `strategy.py` now computes `asr` in Python from integer counts — no SQL type-system dependency. The duplicate unique constraint on `ClusterSummary.cluster_id` is removed. The seeded-data aggregation test calls the router function directly with the test session, correctly verifying the SQL computation. Remaining findings are all warning/minor — acceptable to proceed.

---

## Correctness

**B1 — RESOLVED.** `strategy.py` no longer uses `func.avg(boolean)`. `asr` is computed as `total_successes / total_runs` in Python after the query. Python-side sort replaces the SQL `order_by` on the computed expression. Correct.

**W2 — RESOLVED.** `ClusterSummary.cluster_id` `mapped_column` no longer carries `unique=True`. The named `Index` in `__table_args__` is the sole unique constraint. ORM and Alembic migration are now consistent.

**W1 — `api/routers/runs.py:38-56` — N+1 query, open (warning)**
Not addressed in this pass — accepted as follow-up. For the first attack session (likely <1000 runs), performance is acceptable. Should be resolved before portfolio presentation.

**W3 — `db.py` — dead exports, open (minor)**
`get_db_session` and `init_db` remain. No runtime impact. Follow-up item.

**W4 — `corpus/constants.py` — field names unverified, open (warning)**
Still unverified against the live dataset. Will surface immediately on first `uv run seed-corpus` if wrong. Acceptable — the loader skips malformed rows and logs a warning, so the failure mode is visible.

---

## Style

**S1 — OPEN (minor).** `classifier.py:46-47` dead guard remains. No impact.

**S2 — OPEN (minor).** `SampleReview.tsx:13` redundant null coalescing. No impact.

---

## Tests

**T1 — RESOLVED.** `test_api.py` now has `test_strategy_comparison_computes_asr` — seeds 1 attack + 2 runs (1 success, 1 failure), calls `get_strategy_comparison(db=db_session)` directly, asserts `asr == total_successes / total_runs` to 3 decimal places. Correctly exercises the SQL and the Python computation. The `>=` assertion on `total_runs` and `total_successes` (rather than `==`) is robust to other seeded data in the shared test DB session — correct approach.

**T2 — OPEN.** `run_session()` integration test. Follow-up.

**T3 — OPEN.** TypeScript component tests beyond the tab bar render. Follow-up.

---

## Refactor Candidates

Same as pass 1: R1 (N+1 JOIN), R2 (no longer relevant — asr is now Python-side), R3 (dead db.py exports), R4 (shared table styles in frontend).

---

## Verdict

**PASS WITH NOTES** — All blocking and convention-required items resolved. Open items (W1, W3, T2, T3, S1, S2) are follow-up pass work and do not block the first attack session.

## Handoff

No next role required. Human may proceed to first attack session:

```bash
cd projects/red-team-platform
docker compose up -d
uv run alembic upgrade head
uv run seed-corpus   # verify corpus/constants.py field names from log output
uv run attack
uv run cluster       # after attack session
cd web && pnpm dev   # frontend
```

Follow-up implementer pass (non-blocking): W1 (N+1 in list_runs), W3 (dead db.py exports), T2 (run_session test), T3 (TS component tests).
