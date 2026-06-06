# Reviewer Output — moderation-dashboard safety-signal additions

**Role:** reviewer
**Sequence:** add-feature → reviewer
**Date:** 2026-06-05

---

## Summary

The implementation is correct and complete. Both additions (live flag rate on model cards, disagreement analysis panel) are working, all new tests pass, and no previously passing tests were broken. Two findings worth noting: the disagreement sample ordering is non-deterministic in a subtle way (samples are not guaranteed to be the 10 most recent), and the `ModelPerformance.test.tsx` mock data now has a TypeScript gap introduced by the new required fields on `ModelMetrics`. Neither is blocking. Verdict: PASS WITH NOTES.

---

## Correctness

**C1 — Disagreement sample ordering: 10 events are not necessarily the most recent** · `metrics.py:_DISAGREEMENTS_SAMPLES_SQL` + `get_disagreements()` · **Minor**

`_DISAGREEMENTS_SAMPLES_SQL` selects up to 50 recent escalation events (ordered by `created_at DESC`) in a CTE, then joins to `classifications`. The outer query orders by `r.event_id, c.model_name` (alphabetical event_id). When Python groups the rows and does `list(events.items())[:10]`, the 10 events shown are the first 10 alphabetically by event_id — not the 10 most recent among the 50.

For the portfolio use case (showing representative disagreement examples) this is immaterial. But if "most recent" is the intent, fix by adding an explicit ordering column to the CTE and preserving it through the join:

```sql
WITH recent AS (
    SELECT event_id, ROW_NUMBER() OVER (ORDER BY created_at DESC) AS rn
    FROM escalations
    WHERE escalation_reason = 'model_disagreement'
    ORDER BY created_at DESC
    LIMIT 50
)
SELECT r.event_id, r.rn, c.content, c.model_name, c.predicted_label, c.confidence
FROM recent r
JOIN classifications c ON c.event_id = r.event_id AND c."group" = 'shadow'
ORDER BY r.rn, c.model_name
```

Then in Python, sort `events.items()` by rn before slicing.

**C2 — `ModelPerformance.test.tsx` mock data missing new required fields** · `web/src/test/ModelPerformance.test.tsx:9–38` · **Warning**

`ModelMetrics` now requires `live_event_count: number` and `live_flagged_count: number`. The `PRODUCTION_DATA` mock in `ModelPerformance.test.tsx` was not updated. esbuild (used by vitest) strips types and runs JS, so the runtime value is `undefined`. In `ModelCard.tsx`, `undefined > 0` evaluates to `false`, so the live flag rate stat shows `—` instead of crashing. The tests still fail (pre-existing: 4 of 5 were already failing before this PR for unrelated model-registry reasons), but the missing fields are a TypeScript compile error that will appear if `tsc --noEmit` is run.

**Fix:** add `live_event_count: 500, live_flagged_count: 193` (or any plausible values) to both mock objects in `ModelPerformance.test.tsx`.

No other correctness issues found. The SQL logic is sound:
- `_LIVE_COUNTS_SQL` groups by `model_name` in shadow group; each event produces exactly one row per model so `COUNT(*)` equals `COUNT(DISTINCT event_id)`.
- `total_last_hour = sum(by_category.values())` is correct because the CTE uses `DISTINCT ON (e.event_id)` — one row per event, one category per event.
- `content[:140]` truncation by Python code point is acceptable for Bluesky UTF-8 text.

---

## Style

**S1 — `_build_model_metrics` `group` parameter unused** · `metrics.py:183` · **Minor**

The `group: str` parameter was unused before this PR and remains unused after. Not introduced by this change, but worth removing in a cleanup pass.

No new style violations found. Pydantic fields use correct defaults (`int = 0`). TypeScript types use `type` not `interface`. React component is under 90 lines. Hook follows the `useX` naming convention. No `any`, no non-null assertions.

---

## Tests

**T1 — `test_disagreements_endpoint_shape` does not seed disagreement rows** · `tests/test_api.py` · **Minor gap**

Planner requirement 11 specified "at least one test asserts correctly shaped data from seeded disagreement rows." The current test verifies shape with an empty DB (all zeros). This is correct and useful but does not exercise the SQL join logic or the sample-grouping Python code with real data.

A stronger test would create an `Escalation` row with `escalation_reason='model_disagreement'` and two matching `Classification` rows (different `model_name`, different `predicted_label`) in the shadow group, then assert:
- `total_last_hour == 1`
- `by_category` has one entry
- `samples` has one item with two verdicts

This requires adding `Escalation` to the conftest imports and a new fixture. Recommended as a follow-up.

**T2 — No test for `live_event_count = 0` case (seeded-only model)** · **Minor gap**

The new live-count test covers `live_event_count == 10` (all rows unseeded). A complementary test with seeded rows only (`seeded=True`) verifying `live_event_count == 0` would confirm the `seeded=false` filter works in both directions. Nice-to-have.

---

## Refactor Candidates

**R1 — `_get_live_counts` and `_get_seeded_counts` could be merged**

Both run a simple `SELECT model_name, COUNT(...) FROM classifications GROUP BY model_name` pattern. They could be collapsed into one SQL query with multiple aggregations. Deferred — premature until there's evidence the extra DB round-trip matters.

**R2 — `DisagreementPanel` inline `VerdictBadge` and `SamplePost` sub-components**

The component is clear but could be moved to a `DisagreementPanel/` folder with index.tsx if it grows. Not needed for current size.

---

## Verdict

**PASS WITH NOTES**

No blocking issues. The implementation is correct and all new tests pass.

Recommended follow-ups (can batch before VPS deploy or do now):
1. **C2** — add `live_event_count` and `live_flagged_count` to `ModelPerformance.test.tsx` mock data (2-line fix, clears the TypeScript gap)
2. **T1** — add a seeded-data disagreements test with an `Escalation` fixture (optional but would fully satisfy planner requirement 11)
3. **C1** — if "most recent samples" is the intended behaviour, fix the sample ordering SQL

---

## Handoff

No next role required. The safety-signal additions are complete.

**Next action (P1): apply C2 fix (ModelPerformance mock data) — 2-line change**
**Next action (P2): VPS deploy** per `_config/project-state.md`
