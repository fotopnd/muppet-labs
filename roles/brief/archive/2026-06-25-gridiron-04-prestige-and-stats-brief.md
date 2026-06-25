## Project Name
Gridiron

## Description
Surface coach prestige and add points scored/allowed to the coach season history. Update CoachPage to display prestige visually and extend the season stats table with points columns. Add prestige to the StaffTab (unit 01) for at-a-glance context.

## Language(s)
Python (FastAPI), TypeScript (React)

## Success Criteria
- `GET /coaches/{id}` season rows include two new integer fields: `points_scored` and `points_allowed`
- CoachPage season history table shows Pts and PA columns alongside existing columns
- CoachPage header shows a prestige badge: one filled star per prestige level (1–5), e.g. ★★★☆☆
- StaffTab in ProgramDetail shows prestige stars next to each coach name
- `pnpm build` passes with no TypeScript errors

## Constraints

**Points scored / allowed:**
Extend the `play_stats` CTE in `gridiron/api/routers/coaches.py` `get_coach()`:
```sql
-- points scored = sum of score increments on offense
-- Simplest approach: read final score per game from the games table
-- Add a third CTE or join to games directly:
SELECT cg.season,
    SUM(CASE WHEN cg.team_side = 'home' THEN g.home_score ELSE g.away_score END) AS points_scored,
    SUM(CASE WHEN cg.team_side = 'home' THEN g.away_score ELSE g.home_score END) AS points_allowed
FROM coach_games cg
JOIN games g ON g.id = cg.game_id
GROUP BY cg.season
```
Join this result into the existing final SELECT alongside `wl` and `play_stats`.

**Schema updates:**
- Add `points_scored: int` and `points_allowed: int` to `CoachSeasonRow` in `gridiron/api/schemas.py`
- `CoachDetail` already has `prestige` after unit 02 — no change needed there

**Frontend — CoachPage:**
- Add `points_scored` and `points_allowed` to the `CoachSeasonRow` type in `web/src/types.ts`
- Add `Pts` and `PA` columns to the season table in `web/src/pages/CoachPage.tsx`
- Add prestige stars to the header card: render `prestige` filled stars + `(5 - prestige)` empty stars using `★` / `☆` characters. Use `text-yellow-400` for filled, `text-text-muted` for empty.

**Frontend — StaffTab (ProgramDetail.tsx):**
- The StaffTab was added in unit 01. In this unit, add prestige stars next to each coach name.
- `useProgramCoaches` already returns `ProgramCoach` objects. Add `prestige: number` to the `ProgramCoach` type if not already present (it should be, since the endpoint now reads from coaches which has prestige after unit 02 — verify and add if missing).

## Out of Scope
- `alembic/` — no migrations (prestige column added in unit 02)
- `gridiron/engine/` — not touched
- Recruiting mechanic — deferred
- Booster influence — deferred
- Any coach attribute (run_tendency, style) display in the UI — deferred

## Assumptions
- Unit 01 (staff-tab) and unit 02 (coach-attributes-schema) are both merged before this unit runs
- This unit is parallel-safe with unit 03 (engine-coach-influence) — no shared files
- `coach_games` CTE in `get_coach()` already joins games and knows `team_side` (home/away) — it does, per the existing implementation

## Handoff
Merge to main. All coach sprint units complete. Verify: navigate to a coach page with completed games and confirm points_scored/points_allowed appear, prestige stars render, and StaffTab shows stars on the program page.
