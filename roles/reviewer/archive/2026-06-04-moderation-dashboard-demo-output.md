# Reviewer Output — moderation-dashboard-demo (implementer-fixes-2)

**Role:** reviewer
**Sequence:** implementer-fixes-2 → reviewer
**Date:** 2026-06-04

---

## Summary

All four targeted findings (C1, C2, T1, T2) from the previous reviewer pass are correctly resolved: the idempotency guard, timestamp backdating, and both test files are present and all 41 tests pass. One warning needs attention before the seeded-DB snapshot is taken for VPS deploy: the idempotency DELETE fires before the checkpoint-presence check, so running seed-sim with an unconfigured fine-tuned model silently purges previously seeded rows for that model and writes nothing back. One ruff import-sort violation should be fixed (auto-fixable). Remaining gaps are minor and can be deferred post-deploy.

---

## Correctness

**C1 — Finetuned early-return: idempotency DELETE fires before checkpoint check** · `seed_sim.py:65–129` · **Warning**

The DELETE at line 65–70 runs unconditionally at the top of `seed_model()`. For finetuned models, the checkpoint presence check is at line 123 (`if checkpoint_path is None: return 0`). Execution path for an unconfigured finetuned model:

1. DELETE all seeded rows for `model_name = 'finetuned_distilbert'` → rows gone
2. Log `"skipping finetuned_distilbert (no seeded data for this model)"` → returns 0

If the operator runs `seed-sim --confirm` (or `--models finetuned_distilbert`) without `DISTILBERT_CHECKPOINT_PATH` set after a previous successful seed, the existing finetuned seeded rows are silently destroyed. The only log output says "skipping" — it does not say "deleted N rows." This is the most likely operator mistake before a VPS deploy.

**Fix:** either (a) move the DELETE inside a branch that only executes when the classifier is going to be built (i.e. after line 129, inside the else path), or (b) log the deleted row count before returning:

```python
# option (b) — minimal change
result = session.execute(
    text("DELETE FROM classifications WHERE seeded = true AND model_name = :mk RETURNING id"),
    {"mk": model_key},
)
deleted_count = len(result.fetchall())
if deleted_count:
    logger.info("[%s] Deleted %d previously seeded rows", model_key, deleted_count)
session.commit()
```

Then at the early return: `logger.warning("... skipping %s — %d previously seeded rows were already deleted", model_key, deleted_count)`.

**C2 — Timestamp computation: `seed_base_time` anchored per model, not per session** · `seed_sim.py:153` · **Minor**

`seed_base_time = datetime.now(UTC) - timedelta(hours=24)` is computed inside `seed_model()`. When seeding 5 models in sequence over several hours, each model's 24h window is independently anchored. Model 1 (anchored at T+0h), model 5 (anchored at T+3h) — rows overlap in the analytics window but don't share a common epoch. This is acceptable (each model's own trend is visible), but means the inter-model timestamp alignment is off by the wall-clock time of the seed run. Not a problem at demo scale. Noted in case the operator interprets category-trend charts as cross-model synchronized events.

---

## Style

**S1 — `test_admin.py:8`: ruff I001 import sort violation** · **Minor**

`from sqlalchemy import delete as sa_delete, select` triggers I001 (un-sorted import block). This should have been caught by `ruff check` before handoff. Auto-fixable:

```
uv run ruff check --fix tests/test_admin.py
```

All other files (`seed_sim.py`, `test_cases.py`) pass ruff clean.

---

## Tests

**T1 — `GET /cases` action-populated path not covered** · `test_cases.py` · **Minor gap**

`test_list_cases_returns_content` checks `case["action"] is None`. The `LEFT JOIN case_decisions` path where a decision already exists (and `action` should be `"approved"` or `"rejected"`) is not verified via a subsequent `GET /cases` call. The POST endpoint is tested, but the JOIN result back through GET is not.

**T2 — `no_escalation` filter not covered** · `test_cases.py` · **Minor gap**

`_CASES_SQL` includes `WHERE e.escalation_reason != 'no_escalation'`. No test inserts a `no_escalation` escalation and verifies it's absent from `GET /cases`. The filter is correct by inspection, but the branch is unexercised.

---

## Refactor Candidates

**R1 — Delete-then-early-return ordering in `seed_model()`** · `seed_sim.py:65–129`

This is the structural root of C1. Long-term fix: separate the concerns — have a `clear_seeded(model_key, session_factory)` helper that the caller invokes only after confirming the model is runnable. The early-return guard could then live before any data mutation.

**R2 — `n_rows = max(len(rows) - 1, 1)` single-row edge case** · `seed_sim.py:154`

With `len(rows) == 1`, the single row gets `created_at = seed_base_time` (24h ago, never at `now`). Harmless in production (10 000 rows) but would confuse a unit test of the timestamp logic. Not worth fixing now.

---

## Verdict

**PASS WITH NOTES**

C1 (finetuned delete-without-warning) should be resolved before taking the seeded-DB pg_dump snapshot for VPS restore — if a fine-tuned checkpoint isn't configured at snapshot time, the operator might not notice the rows were silently deleted. S1 (ruff import sort) is a one-command fix. T1 and T2 are acceptable post-deploy gaps.

---

## Handoff

**Recommended next action:** apply two targeted fixes, then proceed to deploy:

1. **C1** — add a RETURNING-based log to the idempotency DELETE in `seed_sim.py` so the operator can see if rows were purged before a skip
2. **S1** — run `uv run ruff check --fix tests/test_admin.py` (one-liner)

These can be done as a micro implementer pass or inline before committing. The deploy sequence should then proceed:
- Push moderation-dashboard to public GitHub repo
- SSH to Hostinger VPS, deploy via Docker Compose
- Run `seed-sim --confirm` on VPS to populate the DB
- `pg_dump` the seeded state for a restore snapshot
- Configure nginx reverse proxy
- Confirm live URL end-to-end
