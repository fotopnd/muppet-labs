# Planner Output — gridiron: staff-tab (unit 01)

**Role:** planner
**Sequence:** add-feature (feature-sprint unit 01)
**Date:** 2026-06-25

---

## Project

`gridiron-staff-tab` — Add a Staff tab to ProgramDetail showing the coaching staff for a program, linked to individual coach pages.

---

## Requirements

1. `GET /programs/{program_id}/coaches` returns 200 with a JSON array of coach objects.
2. Each coach object contains: `coach_id`, `first_name`, `last_name`, `full_name`, `role`, `rating`.
3. `GET /programs/{program_id}/coaches` returns 404 if the program does not exist.
4. `GET /programs/{program_id}/coaches` returns an empty array if the program exists but has no coaches.
5. `ProgramCoach` Pydantic schema added to `gridiron/api/schemas.py`.
6. Endpoint registered on the existing programs router in `gridiron/api/routers/programs.py`.
7. `ProgramCoach` TypeScript type added to `web/src/types.ts`.
8. `useProgramCoaches(programId: number)` hook added to `web/src/api/hooks.ts`.
9. ProgramDetail.tsx gains a fourth tab labelled "Staff".
10. StaffTab renders coaches grouped by role order: Head Coach → OC → DC → ST → others.
11. Each coach name is a `<Link to={/coaches/${coach.coach_id}}>` link.
12. Rating displayed as integer 0–100 (round(rating * 100)).
13. `pnpm build` exits 0 with no TypeScript errors.

---

## Technology Stack

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 + TypeScript | existing project |
| Package manager | uv (backend) / pnpm (frontend) | existing project |
| Key libraries | FastAPI, SQLAlchemy async, Pydantic v2, React Query, React Router | existing project |

---

## Files Changed

| File | Change |
|------|--------|
| `gridiron/api/routers/programs.py` | Add `GET /{program_id}/coaches` route |
| `gridiron/api/schemas.py` | Add `ProgramCoach` schema |
| `web/src/types.ts` | Add `ProgramCoach` type |
| `web/src/api/hooks.ts` | Add `useProgramCoaches` hook |
| `web/src/pages/ProgramDetail.tsx` | Add `'staff'` tab + `StaffTab` component |

---

## Open Questions for Architect

None. Pattern is established — mirror `GET /{program_id}/roster` in programs.py.

---

## Handoff

Next role: architect. Read `gridiron/api/routers/programs.py` for the existing sub-resource pattern, `gridiron/api/schemas.py` for schema conventions, and `web/src/pages/ProgramDetail.tsx` for the tab pattern. No schema migration needed.
