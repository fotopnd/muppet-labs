# moderation-dashboard — Reviewer Issues (2026-06-03)

Logged from `roles/reviewer/output/output.md`. Implementer picks these up in order.
Branch: `moderation-dashboard-review-fixes`

---

## Priority order

| # | ID | File | Severity | Summary |
|---|----|------|----------|---------|
| 1 | W1 | `moderation_dashboard/consumers/base.py:78` | warning | Hardcoded `"moderation-production"` string determines `group` column — data corruption risk if naming changes |
| 2 | T1 | `tests/test_api.py:29` | warning | `assert data["total_events"] >= 0` is always true — change to `== 15` |
| 3 | T2 | `web/src/test/` (missing) | warning | `ModelComparison.test.tsx` not written |
| 4 | T3 | `tests/test_anomaly.py` (missing) | warning | No unit tests for `_compute_zscore` and `_window_boundary` |
| 5 | W2 | `moderation_dashboard/escalation/service.py` | warning | Escalation poll inner loop doesn't check `self._running` — can't be shut down cleanly mid-cycle |
| 6 | M1 | `moderation_dashboard/api/routers/metrics.py:75–88` | minor | `_COMPARISON_META_SQL` and `_GROUND_TRUTH_SQL` constants defined but never used |
| 7 | R1 | `moderation_dashboard/escalation/service.py` + `dbt/` | refactor | Skip-records in `escalations` table couple service logic to dbt SQL — replace with `evaluated_events` table |

---

## Issue details

### W1 — Hardcoded group string in BaseConsumer

**File:** `moderation_dashboard/consumers/base.py:78`

```python
# current
group = "production" if self._group_id == "moderation-production" else "shadow"
```

**Fix:** Add `mode: Literal["production", "shadow"]` to `BaseConsumer.__init__` (after `group_id`). Store as `self._group = mode`. Remove the string comparison in `run()`. Update `runner.py` to pass `mode=args.mode`.

---

### T1 — Weak assertion in stream metrics test

**File:** `tests/test_api.py:29`

```python
# current
assert data["total_events"] >= 0

# fix
assert data["total_events"] == 15  # seeded_classifications inserts 15 rows
```

---

### T2 — Missing ModelComparison test

**File:** `web/src/test/ModelComparison.test.tsx` (create new)

Mirror `ModelPerformance.test.tsx` but mock `GET /metrics/shadow` instead of `/metrics/production`. Cover: cards rendered, active badge, pending badge, "Awaiting checkpoint", error state.

---

### T3 — Missing anomaly detector unit tests

**File:** `tests/test_anomaly.py` (create new)

Test the pure functions without Kafka/Postgres:

- `_compute_zscore`: history < 2 → 0.0; std = 0 → 0.0; normal case → correct value
- `_window_boundary`: given a known datetime, returns correct (window_start, window_end) pair where `window_end - window_start == window_minutes * 60s`
- `_check_signal`: with < `min_history` windows, no flag is written; with >= `min_history` and |z| > threshold, `_write_flag` is called

Instantiate `RollingWindowDetector` with mocked `self._Session` (like `_FakeConsumer` pattern in `test_consumers.py`).

---

### W2 — Escalation inner loop doesn't check shutdown flag

**File:** `moderation_dashboard/escalation/service.py` inside `_poll_cycle`

```python
# add at top of for loop
for event_id in event_ids:
    if not self._running:
        break
    ...
```

---

### M1 — Dead SQL constants

**File:** `moderation_dashboard/api/routers/metrics.py:75–88`

Remove `_COMPARISON_META_SQL` and `_GROUND_TRUTH_SQL`. The actual queries are inlined in `get_comparison()`.

---

### R1 — Skip-record pattern (defer if timeline is tight)

**Files:** `moderation_dashboard/escalation/service.py`, `moderation_dashboard/api/models.py`, `dbt/models/marts/fct_escalation_rates.sql`

Replace skip-records with a dedicated dedup table:

```python
# new ORM model in api/models.py
class EvaluatedEvent(Base):
    __tablename__ = "evaluated_events"
    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

`_get_unevaluated_event_ids()` joins against `evaluated_events` instead of `escalations`. The service writes to `evaluated_events` for ALL processed events, and to `escalations` only when escalating. `fct_escalation_rates.sql` removes the `WHERE escalation_reason != 'no_escalation'` filter.

Requires an Alembic migration for the new table.
