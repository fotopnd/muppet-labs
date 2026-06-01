# Reviewer — case-queue

**Sequence:** `new-project-full` | **Role:** reviewer | **Step:** 5 of 6  
**Date:** 2026-06-01  
**Reads:** `roles/implementer/output/output.md`, all code files in `projects/case-queue/`  
**Resources:** `resources/python-conventions.md`, `resources/typescript-conventions.md`

---

## Summary

case-queue is working software: the FastAPI backend is correctly structured, the async session/commit flow is sound (the flagged double-commit concern is not real — see C1), and the React frontend builds cleanly with 11/11 frontend tests passing. Two ruff findings will block a clean `ruff check` pass before merge: UP042 flags all five `(str, enum.Enum)` enums, and F401 flags an unused import in conftest.py. Beyond those, the main gaps are: unparameterized `dict` / `list` return types, a missing `raise ... from exc` in deps.py, and a systemic `interface` vs `type` violation in the TypeScript types file. None of these block functionality, but the ruff issues must be fixed before the implementer can claim "ruff check clean."

---

## Correctness

### C1 — `decisions.py` flush/commit flow is correct (implementer concern resolved) (Severity: None)

**File:** `api/app/routers/decisions.py:52`, `api/app/database.py:36`

The implementer flagged a potential double-commit. This is not a bug. `get_db()` commits once, after the handler yields (line 36 of `database.py`). The `await db.flush()` in `decisions.py:52` sends the INSERT SQL to the DB within the open transaction so that the immediately following `await db.refresh(decision)` can re-read the new row. `flush()` does not commit — it is a within-transaction operation. The single commit fires when the handler returns normally and the async context manager in `get_db` exits. This is idiomatic SQLAlchemy async usage. No fix required.

### C2 — Five enums use `(str, enum.Enum)` — ruff UP042 will flag (Severity: Blocking for clean ruff pass)

**File:** `api/app/models.py:16, 25, 31, 38, 44`

`CaseCategory`, `Severity`, `CaseStatus`, `Action`, `ActorRole` all use `class Foo(str, enum.Enum)`. `python-conventions.md` requires `StrEnum` (Python 3.11+). Ruff UP042 is active (UP rules selected, target py312). All five will be flagged. Fix: `from enum import StrEnum` and change each class to `class Foo(StrEnum)`, removing the `str` mixin.

### C3 — Unused import in conftest.py — ruff F401 will flag (Severity: Blocking for clean ruff pass)

**File:** `api/tests/conftest.py:13`

`from app.database import _session_factory` is imported at module level but never used directly. The `client` fixture imports `app.database as db_module` inside the function body and uses `db_module._session_factory`. Ruff F401 will flag the top-level import. Fix: remove line 13.

### C4 — `raise HTTPException` in `get_actor` missing `from None` (Severity: Low)

**File:** `api/app/deps.py:22`

```python
except ValueError:
    raise HTTPException(status_code=400, detail=f"Invalid role: {x_actor_role!r}")
```

Convention: "Use `from exc` or `from None` on all re-raises inside `except` blocks." Since the `ValueError` carries no relevant context for the caller (it will be swallowed by FastAPI's exception handler), `raise HTTPException(...) from None` suppresses the implicit exception chain. Fix: `raise HTTPException(...) from None`.

### C5 — `meta: Mapped[dict]` and `meta: dict` are unparameterised (Severity: Low)

**Files:** `api/app/models.py:73`, `api/app/schemas.py:52`

Both use bare `dict`. Convention: "Use `dict[K, V]` (lowercase)." `meta` is a JSONB field holding arbitrary external data — `dict[str, Any]` is correct here (and is acceptable per the convention: "Never use `Any` as a field type unless the field genuinely holds arbitrary external data"). Fix: add `from typing import Any` and change both to `dict[str, Any]`.

### C6 — `_build_filters` returns bare `-> list` in both router files (Severity: Low)

**Files:** `api/app/routers/cases.py:66`, `api/app/routers/audit.py:47`

Both `_build_filters` functions have `-> list` with no type parameter. Convention requires parameterised forms. The return type is a list of SQLAlchemy `ColumnElement` expressions. A practical fix: `from typing import Any` and `-> list[Any]` (the precise type is `list[ColumnElement[bool]]` but importing SQLAlchemy internals for a private helper is excessive). Ruff will NOT flag this (ANN rules are not selected), but it's a convention violation.

### C7 — `CaseDetail` and `get_case` return ORM objects typed as Pydantic schemas (Severity: Very Low)

**Files:** `api/app/routers/cases.py:57`, `api/app/routers/decisions.py:54`

Both use `# type: ignore[return-value]` because the function is annotated `-> CaseDetail` / `-> DecisionRead` but returns an ORM model (`Case` / `Decision`). FastAPI's `response_model` handles serialisation via `from_attributes=True`. The correct annotation would be `-> Case` / `-> Decision` at the function level, with FastAPI's response_model doing the schema conversion. The `type: ignore` silences a real type mismatch rather than fixing it. This is a known FastAPI pattern and the runtime behaviour is correct, but it violates the convention that `type: ignore` should come with an explanation comment.

---

## Style

### S1 — `interface` used throughout `types/index.ts` instead of `type` (Severity: Low — systemic)

**File:** `web/src/types/index.ts`

Convention: "Use `type` for shapes and unions. Use `interface` only when declaration merging is intentional." All 7 type definitions in `types/index.ts` use `interface`. None are candidates for declaration merging. Fix: change all 7 to `type`. This is a low-risk mechanical rename.

### S2 — `tsconfig.app.json` missing `exactOptionalPropertyTypes` (Severity: Low)

**File:** `web/tsconfig.app.json`

Convention: "Enable `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes` in addition to strict." `noUncheckedIndexedAccess` is present; `exactOptionalPropertyTypes` is not. Adding it may surface new type errors in optional-field assignments (particularly in filter objects that spread optional properties).

### S3 — ESLint not configured (Severity: Low)

Convention: "Lint with `eslint` (flat config, `eslint.config.ts`)." No ESLint config exists. `pnpm build` passes (tsc only). Not a functionality gap but a convention deviation — portfolio code should show the full toolchain.

### S4 — `CaseQueue.tsx` type assertions on filter change handlers (Severity: Trivial)

**File:** `web/src/pages/CaseQueue.tsx:49, 56, 64`

`handleFilterChange(setCategory as (v: string) => void)` — a type assertion to widen the setter type. Cleaner alternative: the handler receives the string value and explicitly casts at the assignment site (`setCategory(e.target.value as CaseCategory | '')`). Minor.

---

## Tests

### T1 — No test for `date_from` / `date_to` filter on either endpoint (Severity: Low)

**Files:** `api/tests/test_cases.py`, `api/tests/test_audit.py`

`list_cases` and `get_audit_log` both accept `date_from` and `date_to` query parameters. Both are wired through `_build_filters`. Neither has a test. Given that datetime comparison has timezone-awareness implications (the `created_at` column is `DateTime(timezone=True)`), a test using two known timestamps would confirm the filter behaves correctly.

### T2 — No test for submitting a decision on an already-decided case (Severity: Low)

**File:** `api/tests/test_decisions.py`

The API allows multiple decisions on the same case — there is no guard preventing a second approve/reject on an already-resolved case. Whether this is intentional is a product decision, but the behaviour is untested. A test asserting either (a) a second decision is allowed and the status updates again, or (b) a 409 is returned if the case is not `pending`, would document the intended behaviour. Currently the spec is silent.

### T3 — Frontend tests mock hook layer, not network boundary (Severity: Very Low)

**Files:** `web/src/test/*.test.tsx`

Convention: "Mock only at boundaries: API calls (via `msw`) and browser APIs that don't exist in jsdom." Tests use `vi.mock('@/api/cases')` and `vi.mock('@/api/audit')`, which mock the TanStack Query hook layer — one level inside the network boundary. `msw` is not installed. This produces fast, reliable unit tests but does not test the serialisation path from network response → React Query cache → component. Acceptable for a v1 portfolio project but deviates from the stated convention.

### T4 — No test for submit path in `CaseDetail` (Severity: Low)

**File:** `web/src/test/CaseDetail.test.tsx`

Four tests cover loading, content rendering, form presence, and prior decisions. None fires the submit action. `@testing-library/user-event` is installed but unused. A test that types into the notes field, clicks Submit, and asserts `mutation.mutateAsync` was called (or asserts the success banner appears) would cover the primary user interaction.

---

## Refactor Candidates

Notes only — do not implement without a plan.

| # | Location | Suggestion |
|---|----------|------------|
| R1 | `models.py:16–44` | Replace all five `(str, enum.Enum)` with `StrEnum` — required for ruff clean |
| R2 | `conftest.py:13` | Remove unused `_session_factory` import — required for ruff clean |
| R3 | `deps.py:22` | Add `from None` to the `raise HTTPException` re-raise |
| R4 | `models.py:73`, `schemas.py:52` | Parameterise `dict` → `dict[str, Any]` |
| R5 | `cases.py:66`, `audit.py:47` | Parameterise `-> list` → `-> list[Any]` |
| R6 | `types/index.ts` | Rename all `interface` → `type` |
| R7 | `tsconfig.app.json` | Add `exactOptionalPropertyTypes: true` |
| R8 | `routers/cases.py:57`, `routers/decisions.py:54` | Change return type annotation to ORM type; document `type: ignore` or remove it |

R1 and R2 are the only items that affect whether `ruff check app/ tests/` passes. All others are convention correctness and do not affect runtime behaviour.

---

## Verdict

**PASS WITH NOTES**

The project is architecturally sound and functionally complete. The async commit flow is correct. All frontend tests pass and `pnpm build` is clean. The backend has two ruff findings (C2 and C3) that will cause `ruff check` to fail and must be resolved before the implementer can claim a clean linter pass. No finding is blocking for portfolio use or deployment. Recommended next steps are ordered below.

---

## Handoff

**What this output contains:** Full code review across correctness, style, tests, and refactor candidates. Verdict: PASS WITH NOTES.

**Blocking before `ruff check` clean:**
1. Fix C2 — change all five enums from `(str, enum.Enum)` to `StrEnum`.
2. Fix C3 — remove the unused `_session_factory` import from `conftest.py`.

**Recommended follow-on (non-blocking):**
3. Fix C4 — add `from None` in `deps.py`.
4. Fix C5/C6 — parameterise `dict` and `list` return types.
5. Fix S1 — rename `interface` → `type` in `types/index.ts`.
6. Address T2 — add a test to document the multi-decision behaviour.

**Next role:** retro (step 6 of 6). The retro should read this output alongside `roles/implementer/output/output.md` and `_config/project-state.md`.

**Project-state update required:** Update `_config/project-state.md` to record this review verdict, the two blocking ruff items, and that the next role is retro.
