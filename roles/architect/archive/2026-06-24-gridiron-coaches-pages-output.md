# Architect Output — gridiron: Coaches Pages

**Role:** architect
**Sequence:** add-feature
**Date:** 2026-06-24

---

## System Overview

Three backend files + four frontend files. Backend: new `coaches.py` router with one endpoint, two new Pydantic schemas in `schemas.py`, one import line in `main.py`. Frontend: new `CoachDetail` + `CoachSeasonRow` types, one hook, one page component, one route. All stats computed live via SQL CTE from `play_log` + `games`. No migration needed.

---

## Data Models

### Python schemas (`gridiron/api/schemas.py`)

```python
class CoachSeasonRow(BaseModel):
    season: int
    program_name: str
    program_emoji: str
    wins: int
    losses: int
    win_pct: float
    off_yards: int
    pass_yards: int
    rush_yards: int
    def_yards_allowed: int
    sacks: int
    interceptions: int
    games_played: int

class CoachDetail(BaseModel):
    coach_id: int
    first_name: str
    last_name: str
    role: str
    rating: float
    program_id: int
    program_name: str
    program_emoji: str
    conglomerate_code: str
    seasons: list[CoachSeasonRow]
```

### TypeScript types (`web/src/types/index.ts` — append)

```ts
export type CoachSeasonRow = {
  season: number
  program_name: string
  program_emoji: string
  wins: number
  losses: number
  win_pct: number
  off_yards: number
  pass_yards: number
  rush_yards: number
  def_yards_allowed: number
  sacks: number
  interceptions: number
  games_played: number
}

export type CoachDetail = {
  coach_id: int
  first_name: string
  last_name: string
  role: string
  rating: number
  program_id: number
  program_name: string
  program_emoji: string
  conglomerate_code: string
  seasons: CoachSeasonRow[]
}
```

(Fix: `coach_id: int` → `coach_id: number` in TypeScript)

---

## Module Interfaces

### `gridiron/api/routers/coaches.py`

```python
router = APIRouter()

@router.get("/coaches/{coach_id}", response_model=CoachDetail)
async def get_coach(coach_id: int, db: AsyncSession = Depends(get_db)) -> CoachDetail:
    ...
```

SQL: one query that fetches coach info + seasons in a CTE. Two fetches is fine too (coach lookup + season stats). Single query preferred.

**Full SQL:**

```sql
-- Step 1: fetch coach + program info
SELECT c.id AS coach_id, c.first_name, c.last_name, c.role, c.rating,
       c.program_id, p.name AS program_name, p.emoji AS program_emoji,
       cg.code AS conglomerate_code
FROM coaches c
JOIN programs p ON p.id = c.program_id
JOIN conglomerates cg ON cg.id = p.conglomerate_id
WHERE c.id = :cid

-- Step 2: season stats (one row per season for coach's program)
WITH coach_games AS (
    SELECT g.id AS game_id,
           g.season,
           CASE WHEN g.home_program_id = :pid THEN 'home' ELSE 'away' END AS team_side,
           g.home_score, g.away_score
    FROM games g
    WHERE (g.home_program_id = :pid OR g.away_program_id = :pid)
      AND g.status = 'complete'
)
SELECT
    cg.season,
    SUM(CASE WHEN (cg.team_side='home' AND cg.home_score > cg.away_score)
                OR (cg.team_side='away' AND cg.away_score > cg.home_score)
             THEN 1 ELSE 0 END)::int AS wins,
    SUM(CASE WHEN (cg.team_side='home' AND cg.home_score < cg.away_score)
                OR (cg.team_side='away' AND cg.away_score < cg.home_score)
             THEN 1 ELSE 0 END)::int AS losses,
    COALESCE(SUM(CASE WHEN pl.possession = cg.team_side
                       AND pl.play_type IN ('RUSH','PASS_COMPLETE','TACKLE_FOR_LOSS','SACK','TOUCHDOWN')
                      THEN pl.yards_gained ELSE 0 END), 0)::int AS off_yards,
    COALESCE(SUM(CASE WHEN pl.possession = cg.team_side
                       AND pl.play_type = 'PASS_COMPLETE'
                      THEN pl.yards_gained ELSE 0 END), 0)::int AS pass_yards,
    COALESCE(SUM(CASE WHEN pl.possession = cg.team_side
                       AND pl.play_type IN ('RUSH', 'TACKLE_FOR_LOSS')
                      THEN pl.yards_gained ELSE 0 END), 0)::int AS rush_yards,
    COALESCE(SUM(CASE WHEN pl.possession != cg.team_side
                       AND pl.play_type IN ('RUSH','PASS_COMPLETE','TACKLE_FOR_LOSS','SACK','TOUCHDOWN')
                      THEN pl.yards_gained ELSE 0 END), 0)::int AS def_yards_allowed,
    COUNT(CASE WHEN pl.possession != cg.team_side
               AND pl.play_type = 'SACK' THEN 1 END)::int AS sacks,
    COUNT(CASE WHEN pl.possession != cg.team_side
               AND pl.play_type = 'TURNOVER_INTERCEPTION' THEN 1 END)::int AS interceptions,
    COUNT(DISTINCT cg.game_id)::int AS games_played
FROM coach_games cg
LEFT JOIN play_log pl ON pl.game_id = cg.game_id
GROUP BY cg.season
ORDER BY cg.season
```

`win_pct` computed in Python: `round(wins / games_played, 3) if games_played else 0.0`

**Return construction:**

```python
seasons = [
    CoachSeasonRow(
        season=r["season"],
        program_name=coach_row["program_name"],
        program_emoji=coach_row["program_emoji"],
        wins=r["wins"],
        losses=r["losses"],
        win_pct=round(r["wins"] / r["games_played"], 3) if r["games_played"] else 0.0,
        off_yards=r["off_yards"],
        pass_yards=r["pass_yards"],
        rush_yards=r["rush_yards"],
        def_yards_allowed=r["def_yards_allowed"],
        sacks=r["sacks"],
        interceptions=r["interceptions"],
        games_played=r["games_played"],
    )
    for r in season_rows
]
return CoachDetail(**dict(coach_row), seasons=seasons)
```

### `gridiron/api/main.py`

Add to imports: `from gridiron.api.routers import coaches`
Add: `app.include_router(coaches.router)`

### `web/src/api/hooks.ts`

```ts
export function useCoach(coachId: number) {
  return useQuery({
    queryKey: ['coach', coachId],
    queryFn: () => apiFetch<CoachDetail>(`/coaches/${coachId}`),
  })
}
```

Add `CoachDetail` to the import from `@/types`.

### `web/src/pages/CoachPage.tsx`

Layout mirrors `PlayerPage.tsx`:
1. **Header card** — `{coach.program_emoji} {coach.first_name} {coach.last_name}`, role badge, link to program page via `conglomerate_code + program_id`
2. **Season table** — one row per season. Columns: Season, School, W, L, W%, Off Yds, Pass Yds, Rush Yds, Def Yds, Sacks, INT
3. Loading / error states matching PlayerPage

`win_pct` formatted as `.000` (3 decimal places, e.g. `0.750`).

### `web/src/App.tsx`

Add import: `import CoachPage from '@/pages/CoachPage'`
Add route: `<Route path="/coaches/:coachId" element={<CoachPage />} />`

---

## Dependencies

```
coaches.py
  └── depends on: schemas.CoachDetail, schemas.CoachSeasonRow, gridiron.database.get_db

schemas.py
  └── standalone Pydantic models — no new deps

main.py
  └── depends on: coaches.router

CoachPage.tsx
  └── depends on: useCoach hook, CoachDetail type

hooks.ts
  └── depends on: CoachDetail type, apiFetch

types/index.ts
  └── standalone
```

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Error handling | 404 HTTPException if coach not found (match programs.py pattern) |
| win_pct | Computed in Python, not SQL — avoids division-by-zero and float precision issues |
| Empty seasons list | Valid response — coach exists but has no complete games yet |
| ruff | Run `ruff check --fix gridiron/api/routers/coaches.py gridiron/api/schemas.py gridiron/api/main.py` after writing |

---

## Implementation Notes for Implementer

1. Two separate DB calls is fine — coach lookup then season stats with `program_id` from the first result. One CTE query would also work but is harder to debug.
2. `coach_id` in Pydantic must match SQL alias `c.id AS coach_id` — use `model_validate(dict(row))`.
3. TypeScript: `import type { CoachDetail, CoachSeasonRow } from '@/types'` — use `import type` for verbatimModuleSyntax.
4. `win_pct` display: `.toFixed(3)` in TSX, or `(p.win_pct * 100).toFixed(1) + '%'` — pick one and be consistent.
5. Program link in header: `/conference/${coach.conglomerate_code}/programs/${coach.program_id}` — same as PlayerPage.

---

## Handoff

**Next role:** implementer

Execute in order:
1. Add `CoachSeasonRow` + `CoachDetail` to `schemas.py`
2. Create `gridiron/api/routers/coaches.py` with the GET endpoint
3. Register in `main.py` — restart backend, verify `GET /coaches/1301` returns data
4. Add types to `web/src/types/index.ts`
5. Add `useCoach` to `web/src/api/hooks.ts`
6. Create `web/src/pages/CoachPage.tsx`
7. Add route to `App.tsx`
8. Run `pnpm build` — fix any TS errors
9. Run `ruff check --fix` on modified Python files
10. Commit all tracked files
