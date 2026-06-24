# Planner Output — gridiron: Coaches Pages

**Role:** planner
**Sequence:** add-feature
**Date:** 2026-06-24

---

## Project

`gridiron-coaches-pages` — Add `/coaches/:coachId` pages (backend + frontend) showing per-season team stats for the coach's program.

---

## Requirements

1. `GET /coaches/{coach_id}` returns 200 with coach info (id, first_name, last_name, role, rating, program_id, program_name, program_emoji, conglomerate_code) and a `seasons` list.
2. Each season row contains: season, program_name, program_emoji, wins, losses, win_pct, off_yards, pass_yards, rush_yards, def_yards_allowed, sacks, interceptions, games_played.
3. `GET /coaches/{coach_id}` returns 404 for an unknown id.
4. Stats for a season row are computed live from `play_log` JOIN `games` — no new DB table.
5. Frontend route `/coaches/:coachId` renders a page with: header card (name, role, program emoji + link), season stats table (one row per season), loading + error states.
6. `CoachDetail` type added to `web/src/types/index.ts`.
7. `useCoach(coachId)` hook added to `web/src/api/hooks.ts`.
8. Route `<Route path="/coaches/:coachId" element={<CoachPage />} />` added to `App.tsx`.
9. `pnpm build` exits 0 (no TypeScript errors).
10. Backend restarts cleanly after adding `coaches` router to `main.py`.

---

## Stats SQL Logic

- `possession` in `play_log` is `'home'` or `'away'`. Team side is derived: `CASE WHEN home_program_id = coach.program_id THEN 'home' ELSE 'away' END`.
- Off yards: SUM(yards_gained) WHERE possession = team_side AND play_type IN ('RUSH','PASS_COMPLETE','TACKLE_FOR_LOSS','SACK','TOUCHDOWN')
- Pass yards: SUM(yards_gained) WHERE possession = team_side AND play_type = 'PASS_COMPLETE'
- Rush yards: SUM(yards_gained) WHERE possession = team_side AND play_type IN ('RUSH','TACKLE_FOR_LOSS')
- Def yards allowed: same off_yards set but possession != team_side
- Sacks: COUNT WHERE possession != team_side AND play_type = 'SACK'
- Interceptions: COUNT WHERE possession != team_side AND play_type = 'TURNOVER_INTERCEPTION'
- win_pct: wins / NULLIF(games_played, 0) → round to 3 decimal places in Python

---

## Technology Stack

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 + TypeScript | existing project |
| Package manager | uv (backend) / pnpm (frontend) | existing project |
| Formatter/linter | ruff (backend) / tsc (frontend) | existing project |
| Key libraries | FastAPI, SQLAlchemy async, Pydantic v2, React Query | existing project |

---

## Files Changed

| File | Tracked? | Change |
|------|----------|--------|
| `gridiron/api/routers/coaches.py` | ✅ yes | New router — GET /coaches/{coach_id} |
| `gridiron/api/schemas.py` | ✅ yes | CoachSeasonRow + CoachDetail schemas |
| `gridiron/api/main.py` | ✅ yes | Register coaches router |
| `web/src/types/index.ts` | ✅ yes | CoachDetail + CoachSeasonRow types |
| `web/src/api/hooks.ts` | ✅ yes | useCoach hook |
| `web/src/pages/CoachPage.tsx` | ✅ yes | New page component |
| `web/src/App.tsx` | ✅ yes | Route registration |

---

## Open Questions for Architect

None — SQL pattern is confirmed from DB inspection. `possession` is 'home'/'away'. play_type values are known.

---

## Handoff

**Next role:** architect

Architect reads this file + the brief. Key work:
- Read `gridiron/api/routers/programs.py` for the exact router pattern to mirror
- Read `gridiron/api/schemas.py` for the exact schema pattern
- Read `web/src/pages/PlayerPage.tsx` for the exact UI component pattern
- Write the exact SQL query and exact schema fields
