# Reviewer — Model Behaviour Evaluation Harness

**Sequence:** `new-project-full` | **Role:** reviewer | **Step:** 5 of 5  
**Date:** 2026-05-31  
**Reads:** `roles/implementer/output/output.md` + all code files in `projects/eval-harness/`

---

## Summary

The eval-harness is working software: 40 tests pass, ruff is clean, and the CLI entry point resolves. The architecture is faithfully implemented — data models, SQLite storage, heuristic and LLM-as-judge scoring, drift computation, and all four CLI commands are present and correctly wired. Two correctness notes (naive datetimes, mutable-EvalResult anti-pattern) and two test coverage gaps (BOTH-mode merge, judge retry) do not block the harness from functioning but should be addressed before the reviewer considers this production-grade.

---

## Correctness

### C1 — `datetime.utcnow()` produces timezone-naive datetimes (Severity: Low)

**Files:** `eval/models.py:98`, `eval/models.py:104`, `eval/cli.py:170`, `tests/test_db.py:79,147,162`

`datetime.utcnow()` is deprecated in Python 3.12 and returns a naive `datetime` with no timezone info. All stored timestamps are naive UTC, which is consistent within the codebase (ISO-8601 strings in SQLite, read back via `fromisoformat`), so there is no immediate bug. However, comparing or displaying these datetimes alongside timezone-aware values will raise a `TypeError`. Fix: replace with `datetime.now(UTC)` and add `from datetime import UTC` to imports.

### C2 — `EvalResult.run_id` is set to `""` then mutated by caller (Severity: Low)

**File:** `eval/scorer.py:201`, `eval/cli.py:148`

`score_result()` returns `EvalResult(run_id="", ...)` and `cmd_run` immediately does `result.run_id = run.id`. If a future caller omits the mutation, an empty string is silently stored. Pydantic models are not designed to be mutated post-construction. Fix: add `run_id: str` as a parameter to `score_result()` and pass it through directly. A one-line change to the function signature and the call site.

### C3 — `score_result()` BOTH-mode branch falls through when `skip_judge=True` (Severity: Very Low)

**File:** `eval/scorer.py:166`

When `scoring_method=BOTH` and `skip_judge=True`, `j_score` is `None`. The branch `if rubric.scoring_method == ScoringMethod.BOTH and h_score and j_score:` fails, so execution falls to `elif h_score:` at line 186 and appends the heuristic score. This is the correct behaviour, but it is implicit — the fallthrough path is not obvious from reading the branch. Adding a comment or explicit condition would make intent clear, but this is not a bug.

### C4 — `get_run_by_label` uses `LIKE '%label%'` — potential ambiguity (Severity: Very Low)

**File:** `eval/db.py:154`

If two runs share a label substring (e.g. "smoke" and "smoke-2"), `get_run_by_label("smoke")` returns the most recent match, which may not be the intended run. `eval diff` resolves runs first by exact ID, then by label — so `eval diff smoke smoke-2` would match "smoke-2" for the first argument as well (since "smoke" appears in "smoke-2"). For the current CLI UX this is acceptable, but users should be advised to use run IDs for precision.

---

## Style

### S1 — `all_rubrics: dict = {}` is untyped (Severity: Low)

**File:** `eval/cli.py:110`

Should be `dict[str, Rubric]`. `Rubric` is already importable from `eval.models` (added to the top-level import). The local `load_rubric` import inside `cmd_run` makes the type available.

### S2 — Blank line inside `get_run` function body (Severity: Trivial)

**File:** `eval/db.py:145`

```python
def get_run(conn: sqlite3.Connection, run_id: str) -> EvalRun | None:
    ← blank line here
    row = conn.execute(...)
```

Remove the blank line. Ruff did not flag it (it's legal Python), but it's inconsistent with every other function in the file.

### S3 — `score_result()` comment `# caller sets this` on `run_id=""` is a code smell marker (Severity: Low)

**File:** `eval/scorer.py:202`

A comment explaining that a field is intentionally wrong is a sign the design needs the fix described in C2. Remove the comment when fixing C2.

---

## Tests

### T1 — BOTH-mode merge path is not tested (Severity: Medium)

**File:** `tests/test_scorer.py`

Every `score_result()` test uses `skip_judge=True`. The merge logic in `score_result()` (lines 166–189 of `scorer.py`) — where heuristic and judge scores are combined — has zero test coverage. A test should mock `score_llm_judge` and verify: (a) heuristic `passed` wins over judge when definitive; (b) judge `passed` is used when heuristic returns `None`; (c) `score` is averaged from both sides.

### T2 — `score_llm_judge` retry path is not tested (Severity: Low)

**File:** `tests/test_scorer.py`

The retry logic (second API call on malformed JSON) and the final fallback return (`passed=None, score=None`) are not covered. A test mocking `anthropic.Anthropic` with a sequence of responses — first malformed, then valid — would cover this branch. The fallback path (both attempts malformed) should also be tested.

### T3 — `eval diff` and `eval list` CLI commands have no integration test (Severity: Low)

**Files:** `tests/`

The underlying `compute_drift()` is well-tested. The CLI wiring (`cmd_diff`, `cmd_list`) is not. A minimal test using `typer.testing.CliRunner` would confirm the commands exit 0 with correct output shape. Not blocking for v1.

### T4 — `detect_refusal` edge cases not covered (Severity: Very Low)

**File:** `tests/test_scorer.py`

Missing pattern cases: "I'm unable to help" (pattern 2), "I'm not able to assist" (pattern 7), "not going to help" (pattern 4). The existing positive/negative tests are minimal. Adding these would increase confidence in the pattern set.

---

## Refactor Candidates

These are notes only — do not implement without a plan.

| # | Location | Suggestion |
|---|----------|------------|
| R1 | `score_result()` | Add `run_id: str` parameter; remove post-construction mutation in `cmd_run` |
| R2 | `cmd_run` | Type `all_rubrics` as `dict[str, Rubric]` |
| R3 | `models.py` | Replace `datetime.utcnow` with `datetime.now(UTC)` in default factories |
| R4 | `score_result()` | Add explicit comment on BOTH + skip_judge fallthrough (C3) |
| R5 | `db.py` | Remove blank line inside `get_run` body |

R1 and R3 are the highest value. R2, R4, R5 are cosmetic.

---

## Verdict

**PASS WITH NOTES**

The harness runs, all 40 tests pass, and the implementation is complete and correct for its stated scope. No finding blocks use or deployment. C2 (run_id mutation) and T1 (BOTH-mode test coverage) are the highest-value items to address in a follow-up. The rest are cosmetic or very-low-severity.

**Recommended next step:** Address C2 and T1 via the `add-feature` sequence (short — both are single-file changes). Then commit the project branch and merge to main.

---

## Handoff

**What this output contains:** Full code review across correctness, style, tests, and refactor candidates. Verdict: PASS WITH NOTES.

**Next action (human decision):** 
1. Accept as-is and commit to `project/eval-harness` branch, then merge to main. The harness is usable now.
2. Run a targeted `add-feature` pass to address C2 (run_id parameter) and add T1 test coverage, then commit.
3. Do a full smoke test against a live local LLM (requires Ollama or LM Studio running) to validate the end-to-end path before committing.

**Project-state update:** Update `_config/project-state.md` to record this review verdict and the recommended follow-up items before closing the session.
