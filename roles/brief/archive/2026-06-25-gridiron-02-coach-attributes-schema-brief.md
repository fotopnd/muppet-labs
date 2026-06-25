## Project Name
Gridiron

## Description
Add coaching style attributes to the coaches table via an Alembic migration. These columns are read by the sim engine (unit 03) and surfaced in the UI (unit 04). Update `CoachDetail` schema to expose the new fields.

## Language(s)
Python (Alembic, SQLAlchemy, FastAPI)

## Success Criteria
- New migration applies cleanly via `uv run alembic upgrade head`
- `coaches` table has three new columns: `run_tendency` (float, NOT NULL), `style` (text, NOT NULL), `prestige` (smallint, NOT NULL)
- All existing rows seeded with deterministic defaults (see Constraints)
- `CoachDetail` in `gridiron/api/schemas.py` includes `run_tendency: float`, `style: str`, `prestige: int`
- `GET /coaches/{id}` response includes the three new fields without error
- `uv run alembic downgrade -1` reverses cleanly

## Constraints

**Column definitions:**
```sql
run_tendency  FLOAT    NOT NULL  -- 0.0 (pass-heavy) to 1.0 (run-heavy); meaningful for OC role
style         TEXT     NOT NULL  -- OC: 'balanced'|'spread'|'power_run'|'west_coast'|'air_raid'
                                 -- DC: '4-3'|'3-4'|'nickel'|'blitz_heavy'
                                 -- HC/ST: 'balanced'
prestige      SMALLINT NOT NULL  -- 1 (low) to 5 (elite); CHECK BETWEEN 1 AND 5
```

**Seed defaults (run in upgrade, before removing server_default):**
```sql
-- run_tendency: deterministic spread from 0.30 to 0.70 based on id
UPDATE coaches SET run_tendency = ROUND((0.30 + (id % 41) * 0.01)::numeric, 2);

-- style: cycle through options by id
UPDATE coaches SET style = CASE
    WHEN role = 'OC' THEN
        CASE (id % 5)
            WHEN 0 THEN 'balanced'
            WHEN 1 THEN 'spread'
            WHEN 2 THEN 'power_run'
            WHEN 3 THEN 'west_coast'
            WHEN 4 THEN 'air_raid'
        END
    WHEN role = 'DC' THEN
        CASE (id % 4)
            WHEN 0 THEN '4-3'
            WHEN 1 THEN '3-4'
            WHEN 2 THEN 'nickel'
            WHEN 3 THEN 'blitz_heavy'
        END
    ELSE 'balanced'
END;

-- prestige: derived from rating (0.0–1.0 → 1–5)
UPDATE coaches SET prestige = GREATEST(1, CEIL(rating * 5))::smallint;
```

- Add CHECK constraint on prestige: `BETWEEN 1 AND 5`
- Update `CoachDetail` in `gridiron/api/schemas.py` only — do not change `ProgramCoach` (added in unit 01)
- Update the SQL query in `gridiron/api/routers/coaches.py` `get_coach()` to `SELECT` the three new columns and populate them in the returned `CoachDetail`

## Out of Scope
- `web/` — no frontend changes in this unit
- `alembic/versions/` beyond the single new migration file
- `player_game_stats` table — not touched
- Engine files (`gridiron/engine/`) — not touched
- `ProgramCoach` schema — not touched (belongs to unit 01)

## Assumptions
- Unit 01 (staff-tab) is merged to main before this unit runs
- `gridiron/api/routers/coaches.py` `get_coach()` uses a raw SQL SELECT — add the three column names to the existing SELECT list
- The coaches table currently has: id, program_id, role, first_name, last_name, rating, created_at

## Handoff
Merge to main. Units 03 (engine-coach-influence) and 04 (prestige-and-stats) can then run in parallel — they share no files with each other.
