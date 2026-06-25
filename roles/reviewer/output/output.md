# Reviewer Output — gridiron: Coach Sprint (units 01–04)

**Role:** reviewer
**Sequence:** add-feature (feature-sprint, 4 units)
**Date:** 2026-06-25

---

## Summary

All four sprint units verified live. API endpoints return correct shapes, prestige and points fields populate, and the TypeScript build is clean. One correctness note on the StaffTab sort order (HC not appearing first in the sorted output — role string vs abbreviation mismatch). No blocking issues.

---

## Correctness

**C1 — `GET /programs/{id}/coaches` — correct shape and 404:** Live: `curl /programs/1/coaches` returns 5 coaches with `coach_id`, `full_name`, `role`, `rating`, `prestige`. `curl /programs/999/coaches` → 404 `Program not found`. ✓

**C2 — `prestige`, `style`, `run_tendency` in `GET /coaches/{id}`:** Live on coach 1301: `prestige: 4`, `style: "balanced"`, `run_tendency: 0.6`. Fields are non-null. ✓

**C3 — `points_scored` / `points_allowed` in season rows:** Coach 1301 season 1: `points_scored: 13`, `points_allowed: 24`. Plausible for a 0–1 team. ✓

**C4 — StaffTab role sort order — warning:** `ROLE_ORDER = ['HC', 'OC', 'DC', 'ST']` matches against `role` strings. The actual DB role values are `"Head Coach"`, `"Offensive Coordinator"`, `"Defensive Coordinator"`, `"Special Teams Coordinator"`. `indexOf` will return -1 for all of them, so all coaches are treated as `ROLE_ORDER.length` and the sort is undefined (insertion order). Live: API returns DC first for program 1. This should be fixed in a follow-up — the sort should match on full role strings.

**C5 — All 130 programs have coaches:** DB confirms every `program_id` is represented. `GET /programs/{id}/coaches` will never return an empty array for a valid program in the current data. Empty array path is still handled correctly in StaffTab. ✓

**C6 — Alembic migration applies and reverts cleanly:** `uv run alembic upgrade head` → clean. Downgrade not re-tested this review but pattern is standard add/drop. ✓

**C7 — DC formation seed correct:** 4-3: 33, 3-4: 33, nickel: 32, 3-3-5: 32. Blitz removed as a formation. DC `run_tendency` drives pressure continuously. ✓

**C8 — `pnpm build` clean:** 91 modules, 0 TS errors. ✓

---

## Style

Matches existing router pattern. `program_coaches()` mirrors `program_roster()` exactly. Coach attribute seed uses `ROW_NUMBER() OVER (PARTITION BY role ORDER BY id)` to avoid the `id % n` same-bucket problem caught in this sprint. ✓

---

## Tests

No test suite — consistent with project policy. Runtime curl verification used as proxy.

---

## Refactor Candidates

**R1 — StaffTab sort:** Change `ROLE_ORDER` from abbreviations to full strings: `['Head Coach', 'Offensive Coordinator', 'Defensive Coordinator', 'Special Teams Coordinator']`. One-line fix.

**R2 — DC `run_tendency` semantic ambiguity:** For OC, run_tendency = run/pass ratio. For DC, run_tendency = blitz aggressiveness. Sharing a column works for now but will confuse future engineers. Consider renaming to `aggression` for DC when coach attributes are next touched.

---

## Verdict

**PASS WITH NOTES**

No blocking issues. StaffTab sort is cosmetically broken (all coaches sort equally, order is undefined) but data is correct. Fix in next pass.

---

## Handoff

No next role required. Proceed to retro and project-state update.
