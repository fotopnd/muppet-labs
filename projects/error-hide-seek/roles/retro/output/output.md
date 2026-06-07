# Retro — error-hide-seek

**Role:** retro
**Sequence:** `new-project-full` (final step)
**Date:** 2026-06-07

---

## What We Built

error-hide-seek is an adversarial human-uplift evaluation platform. A red-team Claude agent plants subtle factual errors (inverted conclusions, number substitutions, false citations, scope extensions, causal inversions) into AI safety paper abstracts. A blue-team agent assists human reviewers in catching them. The platform measures **human uplift = TPR(human+agent) − TPR(unaided)** across three review conditions.

**Delivery snapshot:**
- 7-table Postgres schema, fully migrated
- FastAPI backend with 6 routers, 2 Claude agent integrations, CLI scripts
- React 19 + Tailwind v4 frontend, 2 pages, 7 components
- 26 backend tests, 15 frontend tests — all passing
- Ruff clean, 0 TypeScript errors, production build exits 0

---

## What Went Well

**Spec to code fidelity was high.** The architect and design-brief phases nailed the core data model. The `DISTINCT ON (paper_id, condition)` pattern for "first completed session per paper" was specified before implementation and worked first-try in production SQL.

**The `NullPool` fix for pytest-asyncio 1.x was the session's key insight.** asyncpg connections bind to the event loop they're created on. With function-scoped event loops per test (pytest-asyncio 1.x default), connection pool reuse across tests causes "Future attached to a different loop" errors. The fix — `NullPool` everywhere in tests + TRUNCATE-based isolation instead of rollback — is a reusable pattern that any async SQLAlchemy project on pytest-asyncio 1.x will hit.

**Tailwind v4 handled cleanly.** Using `@theme` in `index.css` instead of `tailwind.config.js` was the only change needed. The same utility class names work. No workarounds or monkey-patching required.

**Bidirectional scoring rule was the right call.** Allowing `detection_excerpt ⊂ planted_original` OR `planted_original ⊂ detection_excerpt` makes the TP criterion robust without requiring exact-match precision from either the human or the agent. The 15-char minimum prevents trivial single-word false positives.

---

## What Went Wrong

**pytest-asyncio 1.x cost significant time.** We went through four iterations before landing on the working approach. The root cause was each iteration targeting the symptom (event loop mismatch) rather than the mechanism (connection pool lifetime). Earlier identification of `NullPool` as the standard solution for this class of problem would have saved two attempts.

**`alembic init` failed because the directory already existed** (project was partially scaffolded). This forced manual file writing for `alembic.ini`, `env.py`, `script.py.mako`, and the initial migration — which added time but produced no correctness issues.

**`greenlet` was a hidden dependency.** SQLAlchemy async on macOS requires `greenlet>=3.5.1` but doesn't declare it explicitly. The import error only surfaces at runtime, not at install time. Adding it to `pyproject.toml` as an explicit dependency was the right fix, but it wasn't in the architect's dependency list.

**TypeScript 6 deprecations were a surprise.** `baseUrl` is deprecated; `paths` alone requires no `baseUrl`. `allowImportingTsExtensions: true` is required to import `.tsx` files directly. `"types": ["vite/client"]` is required for CSS side-effect imports. None of these are well-documented in a single place — they were discovered via compiler errors.

**pnpm v11 `allowBuilds` syntax changed.** The workspace YAML key syntax for permitting package build scripts changed from prior versions. `msw: set this to true or false` placeholder in the template wasn't caught until `pnpm install` failed.

---

## Engineering Lessons

**1. NullPool + TRUNCATE is the correct pattern for pytest-asyncio 1.x + asyncpg.**

Do not use connection pooling in tests. Do not rely on transaction rollback for isolation (once a handler commits, rollback is a no-op). Instead:
- All test engines: `poolclass=NullPool`
- All test sessions: `TRUNCATE ... RESTART IDENTITY CASCADE` at fixture start

**2. `score_cli` should either reuse `compute_experiment_results` or document the invariant it relies on.**

The CLI computes TPR with `tp_sessions / complete` (all completed sessions), while the API computes it with joined planted-error sessions. These are equivalent only because `POST /sessions` returns 422 when no planted error exists. If that invariant breaks, they diverge silently. Document it or converge.

**3. `compute_experiment_results` needs a numeric regression test.**

The shape test (`test_get_results`) only checks that 3 conditions appear. A fixture that completes sessions with known TP/FP counts and asserts specific uplift values would catch aggregation bugs without touching the LLM path.

**4. Condition assignment edge cases are worth a unit test.**

`_assign_conditions` is pure, stateless, and handles a non-trivial edge (remainder to `human_agent`). It should have a parametrized test for n=1, n=2, n=3, n=7, n=9.

---

## Architectural Decisions That Aged Well

| Decision | Reason |
|----------|--------|
| `altered_abstract` stored at plant time | Avoids reconstructing the doctored abstract from `original_text` + `altered_text` on every request; no reconstruction bugs |
| `POST /sessions` synchronous with LLM call | Simpler frontend (no polling for annotation); acceptable latency for one-at-a-time review workflow |
| Condition assigned at experiment creation, not session creation | Makes condition distribution deterministic and reproducible from the same paper list |
| Blue-team returns `[]` on double failure (non-fatal) | Agent unavailability degrades to unaided condition gracefully; `human_agent` session still works |
| FPR denominator = total detections (not total papers) | Measures annotation precision, not paper-level false positive rate; more informative for comparing conditions |

---

## What I Would Change

1. **Add `test_compute_results_arithmetic`** — seed 3 papers (one per condition), complete them with controlled TP/FP outcomes, assert exact TPR and uplift values.
2. **Convert `score_cli` to use `compute_experiment_results`** via `asyncio.run()` or extract a shared sync aggregation query.
3. **Fix `_build_session_out` to `def`** — no behavior change, but removes misleading `async`.
4. **Add `_assign_conditions` unit test** for n ∈ {1, 2, 3, 6, 7}.
5. **Add `buildSegments` unit tests** for overlapping and unfound annotations.

None of these are blockers. The platform is demo-ready as shipped.

---

## Sequence Completion

| Step | Role | Status |
|------|------|--------|
| 1 | brief | ✓ Complete |
| 2 | planner | ✓ Complete |
| 3 | architect | ✓ Complete |
| 4 | design-brief | ✓ Complete |
| 5 | frontend-architect | ✓ Complete |
| 6a | implementer (backend) | ✓ Complete |
| 6b | implementer (frontend) | ✓ Complete |
| 7 | reviewer | ✓ Complete — PASS WITH NOTES |
| 8 | retro | ✓ Complete |

**Sequence: `new-project-full` — DONE.**

---

## Handoff

No further roles in this sequence. Update `_config/project-state.md` to mark error-hide-seek complete and record the reusable `NullPool + TRUNCATE` pattern as a workspace-level finding.
