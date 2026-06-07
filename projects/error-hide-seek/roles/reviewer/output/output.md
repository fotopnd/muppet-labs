# Reviewer Output — error-hide-seek

**Role:** reviewer
**Sequence:** `new-project-full` (step 7)
**Date:** 2026-06-07

**Reads:**
- `roles/implementer/output/backend-output.md`
- `roles/implementer/output/output.md`
- `error_hide_seek/` and `web/src/` source files

---

## Baseline

| Suite | Result |
|-------|--------|
| `uv run pytest tests/ -q` | **26 passed** in 1.11s |
| `uv run ruff check .` | **0 errors** |
| `uv run ruff format --check .` | **0 changes needed** |
| `pnpm exec vitest run` | **15 passed** in 619ms |
| `pnpm build` | **0 TS errors**, built successfully |

---

## Correctness

**✓ CORRECT — Scoring rule**

`is_true_positive` applies bidirectional substring containment with case-insensitive, stripped comparison. Matches spec. `DetectionIn.min_length=15` enforced in schema layer — `test_detection_min_length_enforced` confirms 422 on short excerpts.

**✓ CORRECT — Uplift metric**

`compute_experiment_results` computes TPR in Python as `detected / planted_count` (integer sums), never `avg(boolean)`. The `DISTINCT ON (paper_id, condition)` subquery with `order_by(completed_at.asc())` correctly selects the first completed session per paper per condition.

**✓ CORRECT — Condition assignment**

`_assign_conditions` uses `n // 3` thirds with `n - 2 * third` remainder assigned to `human_agent`, ensuring all papers get a condition when `n` is not divisible by 3.

**✓ CORRECT — Abstract text returned**

`POST /sessions` returns `pe.altered_abstract` as `abstract_text`, not the original. Human reviewer always sees the doctored version. `test_create_session_unaided` asserts `"degrades alignment by 30%" in data["abstract_text"]`.

**✓ CORRECT — Synchronous POST /sessions**

Session creation waits for blue-team annotation (and auto-scoring for `agent_only`) before returning. LLM client constructed per-request, never at module load.

**⚠️ MINOR — `_build_session_out` spurious `async`**

`sessions.py:26` declares `async def _build_session_out(...)` but contains no `await`. This is a no-op (awaiting a coroutine with no suspensions works), but the `async` keyword is misleading. Safe to convert to `def`.

**⚠️ NOTE — `score_cli` TPR formula diverges from API path**

`scorer.py:207–225` (the CLI) computes TPR using raw SQL: `tp_sessions / complete` where `complete` is all completed sessions. `compute_experiment_results` (the API path) joins to `PlantedError` and only scores sessions that have a planted error. Because `POST /sessions` enforces a `422` when no planted error exists, all completed sessions in practice have a planted error — so both formulas produce the same number. But the divergence is a latent inconsistency: if that invariant ever breaks, the CLI and API could disagree silently.

---

## Style

**✓ ADDRESSED — ruff B-ruleset findings**

- B007 (unused loop var `ep` → `_ep`) — fixed in `plant.py:56`
- B905 (`zip()` without `strict=`) — fixed in `experiments.py:25`
- B008 (`Depends(...)` false positive) — legitimately ignored in `ruff.toml`

**NOTE — No `from __future__ import annotations`**

Not present in any module. Not required for Python 3.12 (forward refs in class bodies resolved natively). Workspace style does not mandate it. No action needed.

**NOTE — String literal for enum assignment**

`sessions.py:121`: `session_row.status = "completed"` instead of `SessionStatus.COMPLETED`. SQLAlchemy accepts raw strings for `StrEnum` columns, so this is not a bug. The consistent style would use the enum member.

---

## Tests

**✓ SOLID — Scoring unit tests**

`test_scoring.py` covers `is_true_positive` in 5 cases (excerpt-in-planted, planted-in-excerpt, case-insensitive, false negative, whitespace) and `score_detections` in 3 cases (one TP + one FP, all FP, empty list). Good coverage of the core algorithm.

**✓ SOLID — API integration tests**

`test_api.py` covers health, paper CRUD, experiment creation, session creation (unaided), review submission, double-submit 409, detection min-length enforcement. All route contracts exercised.

**⚠️ GAP — `compute_experiment_results` arithmetic untested**

`test_get_results` verifies response shape (200, `experiment_id`, 3 conditions) but not computed TPR values. There is no test that seeds a fully-completed experiment with known outcomes and asserts `uplift`, `true_positive_rate`, or `false_positive_rate` numeric values. If the aggregation math regresses, no test catches it.

**⚠️ GAP — `_assign_conditions` untested**

The condition-assignment function is a pure function with a non-trivial edge case (remainder goes to `human_agent`). It has no dedicated unit test.

**NOTE — Frontend segment algorithm untested**

`buildSegments` in `AnnotatedAbstract.tsx` handles overlapping annotations with `coveredUntil` tracking. The existing test checks that highlighted spans render, but doesn't exercise the overlap/ordering edge cases.

---

## Refactor Candidates

| Item | Location | Priority |
|------|----------|----------|
| Convert `_build_session_out` to `def` | `sessions.py:26` | Low |
| Unify CLI and API TPR logic | `scorer.py:191–244` | Low |
| Use `SessionStatus.COMPLETED` (not string literal) | `sessions.py:121` | Low |
| Unit test `_assign_conditions` | `tests/test_api.py` | Low |
| Unit test `compute_experiment_results` with known fixture | `tests/test_scoring.py` | Medium |

---

## Verdict

**PASS WITH NOTES**

No correctness bugs. All 41 tests pass. Linting clean. The implementation is spec-complete and production-ready for a portfolio evaluation.

Two items are worth addressing before a second experiment run:

1. **`test_get_results` gap** — add a fixture that completes sessions with known TP/FP outcomes and assert uplift. This protects the aggregation math.
2. **`score_cli` divergence** — acceptable as-is given the `422` invariant, but document the assumption or converge the formulas.

Everything else is low-priority style cleanup with no functional impact.

---

## Handoff

**Next role:** retro

**Retro reads:**
- This file
- All `roles/*/output/output.md` files in sequence
- `_config/project-state.md`

**Action before retro:** update `_config/project-state.md` to mark error-hide-seek sequence complete.
