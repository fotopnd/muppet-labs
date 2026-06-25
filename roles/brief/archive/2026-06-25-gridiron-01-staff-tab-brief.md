## Project Name
Gridiron

## Description
Add a Staff tab to the program detail page. Requires a new `GET /programs/{id}/coaches` API endpoint that returns the coaching staff for a program. The StaffTab renders coach names (linked to their individual pages), roles, and ratings.

## Language(s)
Python (FastAPI), TypeScript (React)

## Success Criteria
- `GET /programs/{id}/coaches` returns a JSON array of coach objects with fields: `coach_id`, `first_name`, `last_name`, `full_name`, `role`, `rating`
- HTTP 404 if program does not exist
- ProgramDetail.tsx has a fourth tab labelled "Staff" alongside Schedule / Roster / Stats
- StaffTab renders a list grouped by role (Head Coach first, then OC, DC, others alphabetically)
- Each coach name is a link to `/coaches/:id`
- Rating displayed as a 0–100 integer (multiply float by 100, round)
- `pnpm build` passes with no TypeScript errors

## Constraints
- Add the endpoint to `gridiron/api/routers/programs.py` (not coaches.py) — it is a sub-resource of a program
- Add `ProgramCoach` response schema to `gridiron/api/schemas.py`
- Add `useProgramCoaches(programId)` hook to `web/src/api/hooks.ts`
- Add `ProgramCoach` type to `web/src/types.ts`
- Do not change the existing `GET /coaches/{id}` endpoint or `CoachDetail` schema
- Do not add any new columns to the coaches table — this unit uses existing columns only
- Staff tab shows current coaching staff only; no season history in this tab

## Out of Scope
- `gridiron/api/schemas.py` changes beyond adding `ProgramCoach` (coach attribute fields come in unit 02)
- `alembic/versions/` — no migrations in this unit
- `web/src/pages/CoachPage.tsx` — not touched
- `gridiron/engine/` — not touched
- Prestige display — comes in unit 04

## Assumptions
- Gridiron project is at `/Users/fotopnd/Documents/muppet-labs/projects/gridiron/`
- DB: `postgresql+asyncpg://gridiron:gridiron@localhost:5438/gridiron`
- API runs on port 8006; frontend on port 5177 (or next available)
- Each program has 1 Head Coach, 1 OC, 1 DC, 1 ST coach (based on `role` column in coaches table)
- `main.py` already includes the programs router; no router registration change needed

## Handoff
Merge branch to main. Unit 02 (coach-attributes-schema) can then run — it touches `gridiron/api/schemas.py` to add new coach attribute fields, which this unit has already established `ProgramCoach` in.
