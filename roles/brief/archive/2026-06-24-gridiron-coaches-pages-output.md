# Brief — gridiron: Coaches Pages

**Role:** brief
**Sequence:** add-feature
**Date:** 2026-06-24

---

## Project Name
`gridiron-coaches-pages`

## Description

Add a coach detail page at `/coaches/:coachId` (backend + frontend) showing per-season team stats for the coach's program, mirroring the existing player pages pattern.

## Language(s)
Python (FastAPI backend + Pydantic schemas) + TypeScript (React frontend)

## Success Criteria

Done when:
1. `GET /coaches/{coach_id}` returns coach info + list of per-season rows (season, program_name, program_emoji, wins, losses, win_pct, off_yards, pass_yards, rush_yards, def_yards_allowed, sacks, interceptions, games_played).
2. 404 returned for unknown coach_id.
3. `/coaches/:coachId` renders a page styled like PlayerPage: header card (name, role, program link), then a season stats table with all requested columns.
4. Route is registered in `App.tsx`.
5. Backend restarts cleanly; frontend builds without TS errors.

## Constraints

- No new DB tables or migrations — all stats computed live from `play_log` + `games`
- Engine files (`gridiron/engine/`) are gitignored — not touched
- Do not deploy to fotopnd.dev
- Stats must handle coaches with 0 complete games gracefully (empty list)

## Out of Scope

- Linking coaches from program detail pages (follow-up)
- Coach-specific split stats (OC offense only / DC defense only) — show all team stats for all coach roles
- Historical coach transfers between programs

## Assumptions

- `possession` in `play_log` is `'home'` or `'away'` (not program_id) — confirmed from DB query
- Offensive yards = yards from RUSH + PASS_COMPLETE + TACKLE_FOR_LOSS + SACK + TOUCHDOWN where team has possession
- Passing yards = PASS_COMPLETE yards only (clean, user-facing; excludes SACK negatives)
- Rushing yards = RUSH + TACKLE_FOR_LOSS yards
- Defensive yards allowed = same play_type set but opponent has possession
- Sacks = COUNT of SACK plays where opponent has possession (team's defense sacked opponent QB)
- Interceptions = COUNT of TURNOVER_INTERCEPTION where opponent has possession
- Only season 1 in DB currently; query returns one row per season naturally

## Handoff

**Next role:** planner

Planner confirms the SQL approach and the file list.
