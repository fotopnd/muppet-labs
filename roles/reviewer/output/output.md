# Reviewer Output — moderation-dashboard

**Role:** reviewer
**Sequence:** `new-project-full` (step 7)
**Date:** 2026-06-03

---

## Summary

The implementation is solid: architecture spec is followed faithfully, Python passes ruff and TypeScript passes strict-mode tsc with zero errors, and all major system components are present and logically correct. The implementer's four self-flagged concerns are resolved — the ground-truth reconstruction in the comparison endpoint is correct, and the escalation dedup strategy works — but two produce test coverage gaps and structural debt that should be addressed before deployment. No blocking correctness issues found. Recommended next action: address the weak stream metrics assertion (warning) and the hardcoded group-ID string (warning), then proceed to a live integration test.

---

## Correctness

### W1 — Hardcoded `"moderation-production"` string determines `group` column value
**File:** `moderation_dashboard/consumers/base.py:78`
**Severity:** warning

```python
group = "production" if self._group_id == "moderation-production" else "shadow"
```

The group column written to every `classifications` row is determined by string-comparing `self._group_id` to the literal `"moderation-production"`. If the runner ever uses a different group ID convention, all production classifications will silently land in the `shadow` bucket (the else branch) with no error or warning. The runner.py currently constructs `"moderation-production"` correctly, so this works today — but it is fragile.

**Fix:** Accept `mode: Literal["production", "shadow"]` as a second constructor param (or derive it from group_id with an explicit validation), and set `self._group = mode`. Remove the string comparison from `run()`.

---

### W2 — Escalation poll cycle has no internal shutdown check
**File:** `moderation_dashboard/escalation/service.py:70–103`
**Severity:** warning

`_poll_cycle()` processes up to 100 events, each requiring a Postgres query plus an HTTP POST to case-queue. If case-queue is slow (e.g., cold start, overloaded), 100 sequential HTTP calls could take minutes. During this time, `self._running = False` set by SIGINT is not checked. The process can't be shut down cleanly mid-cycle.

**Fix:** Check `self._running` at the top of the inner `for event_id in event_ids:` loop:
```python
for event_id in event_ids:
    if not self._running:
        break
```

---

### M1 — `_COMPARISON_META_SQL` and `_GROUND_TRUTH_SQL` are defined but never used
**File:** `moderation_dashboard/api/routers/metrics.py:75–88`
**Severity:** minor

Two module-level `text()` constants are defined and then replaced by inline `text(...)` calls inside `get_comparison()`. Dead code that will confuse readers.

**Fix:** Remove `_COMPARISON_META_SQL` and `_GROUND_TRUTH_SQL`.

---

### M2 — `FinetunedConsumer.classify()` null-checks `self._pipe is None` which can never be true
**File:** `moderation_dashboard/consumers/finetuned.py:44–46`
**Severity:** minor

The `FinetunedConsumer.__init__` always assigns `self._pipe` — it either loads successfully or raises an exception. `runner.py` exits before constructing the consumer when no checkpoint path is set. The `if self._pipe is None: raise RuntimeError(...)` guard is dead code.

**Fix:** Remove the null-check, or document why it exists (e.g., subclass override scenario).

---

### M3 — Ground-truth reconstruction in `GET /metrics/comparison/{event_id}` is documented but sound
**File:** `moderation_dashboard/api/routers/metrics.py:197–214`
**Severity:** minor (resolved — no action required)

The implementer flagged this as potentially lossy. After analysis: the reconstruction is correct for binary labels. `correct = (predicted_label == ground_truth)` means `ground_truth = predicted_label` when `correct=True`, and `ground_truth = 1 - predicted_label` when `correct=False`. This is lossless for all four combinations of `predicted_label` × `correct`. The LIMIT 1 is consistent because ground_truth is a property of the event, not the model — any row for this event produces the same reconstruction. No fix needed; consider adding a comment to explain the logic.

---

## Style

### S1 — `VITE_CASE_QUEUE_URL` default URL duplicated in two files
**File:** `web/src/api/analytics.ts:5`, `web/src/pages/HumanReview.tsx:6`

```typescript
const CASE_QUEUE_URL = import.meta.env.VITE_CASE_QUEUE_URL ?? 'http://localhost:8000'
```

The same env var read with the same default appears in two separate modules. Convention: environment-variable access should be centralised (e.g., a `web/src/config.ts` module).

---

### S2 — `query.data!` non-null assertion in accumulation hooks
**File:** `web/src/api/production.ts:22`, `web/src/api/shadow.ts:22`

The `!` on `query.data` inside the `setHistory` closure is required because TypeScript can't narrow through the closure boundary. However, a cleaner pattern captures the value before the closure:
```typescript
const data = query.data
if (!data) return
setHistory(prev => {
  for (const m of data) { ... }
})
```
This removes the need for `!` and makes the nullability intent explicit.

---

## Tests

### T1 — `test_stream_metrics_returns_event_rate` assertion is always true
**File:** `tests/test_api.py:29`
**Severity:** warning

```python
assert data["total_events"] >= 0
```

This assertion never fails. The test uses `seeded_classifications` which inserts 15 rows. The correct assertion is `assert data["total_events"] == 15`. The comment acknowledges "rate may be 0" for `event_rate_per_sec` due to timing, but `total_events` counts all-time events and is not time-sensitive.

**Fix:** Change to `assert data["total_events"] == 15`.

---

### T2 — `ModelComparison.test.tsx` not written
**File:** `web/src/test/` (missing)
**Severity:** warning

Acknowledged by implementer. `ModelComparison` uses `useShadowMetrics` (different hook from `ModelPerformance`) and renders the same component tree. Without a test, the shadow-group error path and the 3-column grid layout are untested at the component level.

**Fix:** Add `ModelComparison.test.tsx` mirroring `ModelPerformance.test.tsx` but with `GET /metrics/shadow` as the mocked endpoint.

---

### T3 — No unit tests for `anomaly/detector.py`
**File:** `tests/` (missing)
**Severity:** warning

`_compute_zscore`, `_window_boundary`, and `_check_signal` are pure functions testable without Kafka or Postgres. The Z-score logic in particular is critical to system correctness (determines whether anomaly flags are written) and has no test coverage.

**Fix:** Add `tests/test_anomaly.py` with unit tests for `_compute_zscore` (< 2 history → 0.0, std=0 → 0.0, normal case) and `_window_boundary` (correct epoch math).

---

### T4 — `test_write_result_calls_session` tests implementation, not behaviour
**File:** `tests/test_consumers.py:38–50`
**Severity:** minor

The test asserts that `session.add()` and `session.commit()` are called — this is testing internal method calls, not observable behaviour. Per `python-conventions.md`: "Prefer real objects over mocks." The test should instead verify a row exists in the DB after calling `_write_result`.

---

## Refactor Candidates

### R1 — Skip records in `escalations` table pollute the escalation domain
**File:** `moderation_dashboard/escalation/service.py:87–94`

Writing `escalation_reason="no_escalation"` to the `escalations` table is functional but architecturally messy. The table is supposed to contain escalations; skip records exist only for deduplication. This causes `fct_escalation_rates.sql` to need a filter against the literal string `"no_escalation"` — tight coupling between service logic and dbt SQL.

**Recommendation:** Replace with a separate `evaluated_events(event_id TEXT PRIMARY KEY, evaluated_at TIMESTAMPTZ)` table. The escalation service writes to this table for all evaluated events, and to `escalations` only when escalating. The dbt model joins `events` with `escalations` directly, with no filtering needed.

---

### R2 — `CASE_QUEUE_URL` should be centralised
**See S1.** Extract to `web/src/config.ts`:
```typescript
export const CASE_QUEUE_URL = import.meta.env.VITE_CASE_QUEUE_URL ?? 'http://localhost:8000'
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8002'
```
(`API_URL` is already in `client.ts` — centralise both.)

---

### R3 — `consumers/base.py` group derivation should be explicit
**See W1.** The fix is straightforward and prevents a silent data corruption scenario. Should be treated as the next implementer fix rather than deferred.

---

## Verdict

**PASS WITH NOTES**

No blocking correctness issues. Two warnings should be addressed in a follow-up implementer pass before the system goes into a live demo run:
- **W1** (hardcoded group string) — data corruption risk if group ID convention ever changes
- **T1** (weak stream metrics assertion) — currently a non-assertion that hides test infrastructure issues
- **T2** (missing ModelComparison test) — straightforward to add

The skip-record pattern (R1) and ground-truth comment (M3) are technical debt worth logging but do not block the system from running correctly.

---

## Handoff

**PASS WITH NOTES** — no next role required unless human initiates one.

**Recommended implementer follow-up (priority order):**
1. Fix W1 — replace hardcoded group string with explicit `mode` param in `BaseConsumer`
2. Fix T1 — change `>= 0` to `== 15` in `test_stream_metrics_returns_event_rate`
3. Add T2 — `ModelComparison.test.tsx`
4. Add T3 — `tests/test_anomaly.py` unit tests for pure functions
5. Fix W2 — add `if not self._running: break` to escalation inner loop
6. Fix M1 — remove dead SQL constants
7. Consider R1 — evaluated_events table (architectural, defer if timeline is tight)
