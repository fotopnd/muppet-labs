# Reviewer Output — red-team-platform v5

**Role:** reviewer
**Sequence:** add-feature
**Date:** 2026-06-15

## Summary

The implementation is complete and functionally correct. All five features (case review, audit log, SSE streaming, auto-triage, CI/CD) ship cleanly: `ruff check` and `ruff format --check` both pass, `tsc --noEmit` passes with 0 errors, and 24 backend tests + 5 frontend tests pass (5 pre-existing xfail). The two main issues worth noting are: (1) the SSE `event_generator` loads ALL runs into memory before streaming, which is acceptable at portfolio scale but would not scale; and (2) `SampleOut` was not updated with `triage_tier` (not a functional gap since CaseReview uses `useRuns`, not `useSample`). No blocking issues found.

## Correctness

**C1 — SSE generator memory usage (warning)**
Location: `src/red_team_platform/api/routers/runs.py`, `event_generator()`
The generator calls `.all()` on the result before streaming — loading all 11,688 runs into memory before yielding. For production scale this would be problematic; for portfolio demo it is acceptable. Note in BUILDOUT.md as known limitation.

**C2 — CaseReview dedup mode ignores triage_tier filter (minor)**
Location: `runs.py` `list_runs()`, dedup path
When `dedup=True`, the DISTINCT ON SQL runs via `text()` and bypasses the `triage_tier` filter. Compare mode in CaseReview always requires a `session_id`; triage filtering is more meaningful in All Runs mode. Acceptable for v1.

**C3 — `SampleOut` schema lacks `triage_tier` (minor)**
Location: `src/red_team_platform/api/schemas.py`
`SampleOut` (used by `/sample/{run_id}`) was not updated with `triage_tier`. CaseReview uses `useRuns`, not `useSample`, so no functional gap exists. The field will be `undefined` if anyone uses `SampleOut` directly.

**C4 — Reviewer dropdown in AuditLog is static (acceptable)**
Location: `web/src/pages/AuditLog.tsx`
Reviewer dropdown hardcodes `["analyst-1"]`. Per typescript-conventions "queryable set → dropdown" rule, a `GET /audit-log/reviewers` endpoint would be cleaner. For v1 with a single hardcoded reviewer, static is fine. Note for v2.

## Style

**S1 — `LiveFeed` and `DecisionForm` exceed 60-line guideline (minor)**
Both inline components exceed the ~60 line extract threshold. The EventSource ref pattern in LiveFeed makes extraction awkward. Acceptable in single-file context.

**S2 — `const API = ...` duplicated across new files (minor)**
Four new files redeclare the same API base URL constant. This matches the pre-existing pattern in all existing hooks — not a v5 regression, but worth extracting in a future pass.

## Tests

**T1 — No integration tests for new backend endpoints (note)**
`POST /runs/{run_id}/review`, `GET /runs/{run_id}/review`, `GET /audit-log`, `GET /runs/stream`, `GET /runs/triage-summary` have no tests. Adding smoke tests via the `api_client` TestClient fixture would follow the existing `test_api.py` pattern.

**T2 — No frontend component tests for CaseReview or AuditLog (note)**
Low-effort additions: a basic render test checking triage badge section appears for CaseReview, and that the filter dropdowns render for AuditLog.

## Refactor Candidates

**R1 — Extract shared API base URL constant to `src/lib/api.ts`**
Eliminate 4+ duplicate declarations. Low effort.

**R2 — SSE streaming via cursor or batch fetch**
Replace `.all()` with `stream_results()` for large datasets. Relevant at >100k rows.

**R3 — Literal types for decision and triage_tier in Python schemas**
`decision: str` in `CaseReviewOut` could be `Literal["approve", "flag", "escalate"]`; `triage_tier: Literal["auto_safe", "review", "auto_flag"]` in `RunOut`. Tighter typing.

## Verdict

PASS WITH NOTES

C1 (memory), C2 (dedup/triage mismatch), C3 (SampleOut gap) are all minor v1 acceptances. T1 endpoint tests would strengthen the portfolio — worth adding in a follow-up pass. No blocking issues.

## Handoff

Next role: retro
Write retro output and update `_config/project-state.md` to reflect v5 complete. Capture the following new workspace conventions: xfail pattern for asyncpg bias tests, `compute_triage_tier` as a pattern for computed-at-query-time fields, SSE `StreamingResponse` + async generator pattern.
