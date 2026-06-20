# Roster-Gen Handoff — Implementer → Reviewer

**Date:** 2026-06-20
**Brief:** roster-gen
**Status:** Implementer complete; ready for review

---

## What Was Built

### Files Created

- `/Users/fotopnd/Documents/muppet-labs/projects/gridiron/scripts/seed_roster.py`
  - CLI entrypoint: generates 85 players per program (11,050 total), inserts with TRUNCATE + bulk INSERT
  - Supports `--seed`, `--dry-run`, `--limit N`, `--db-url`
  - Pre-insert validation + post-insert DB validation both pass

- `/Users/fotopnd/Documents/muppet-labs/projects/gridiron/alembic/versions/36a6ee9b555e_players_schema.py`
  - New migration chained after `a1b2c3d4e5f6` (games_schedule_schema)
  - Creates `players` table with all columns, check constraints, FK to programs, and UNIQUE(program_id, jersey_num)
  - Applied successfully; migration is at head (`b2c3d4e5f6a7` staff schema also applied transitively)

### Files Modified

- `/Users/fotopnd/Documents/muppet-labs/projects/gridiron/gridiron/models.py`
  - Added `Float` import
  - Added `Player` SQLAlchemy model (Mapped/mapped_column pattern)
  - Wired back-reference: `Program.players = relationship("Player", back_populates="program")`

- `/Users/fotopnd/Documents/muppet-labs/projects/gridiron/pyproject.toml`
  - Added `seed-roster = "scripts.seed_roster:main"` to `[project.scripts]`

---

## Actual Row Counts (Post-Seed)

| Metric | Expected | Actual |
|--------|----------|--------|
| Total players | 11,050 | 11,050 |
| Programs with exactly 85 players | 130 | 130 |
| Programs with unique jersey sets | 130 | 130 |
| Attribute values in [0,1] | all | all |

### Additional spot-checks

| Check | Result |
|-------|--------|
| Whimsy first-name rate | 5.9% (~expected ~5.5%) |
| Whimsy last-name rate | 5.8% (~expected ~5.5%) |
| Year 1 (freshman) | 4,450 (40.3%) |
| Year 2 (sophomore) | 3,320 (30.1%) |
| Year 3 (junior) | 2,185 (19.8%) |
| Year 4 (senior) | 1,095 (9.9%) |

---

## Deviations From Brief

1. **`alpha`/`delta`/`sigma`/`psi`/`omega` are REAL (float) not SmallInteger 1–100.**
   The brief spec table says SmallInteger range 1–100, but the schema DDL block says `REAL NOT NULL` with no integer constraint. The implementer followed the DDL block (REAL/float in [0.0, 1.0]) as that is authoritative. If the sim-engine expects integers, the migration and model will need to change.

2. **Jersey number strategy: position-range-aware with random selection within range.**
   The brief says "position-range aware" without specifying exact ranges. Ranges were inferred from real college football conventions (e.g., QBs: 1–19, OL: 50–79, DL: 90–99). Falls back to any unused 1–99 if range is exhausted.

3. **`resources/engine-constants.md` not consulted** (it doesn't exist yet per the brief). V1 placeholder used: uniform [0.2, 0.8] with year-based modifiers (+0.05 delta for freshmen, +0.05 sigma for seniors). No Beta distribution applied.

4. **Migration also applied `b2c3d4e5f6a7` (staff_schema)** because it was chained off `36a6ee9b555e` as down_revision. This was pre-existing; no staff data was seeded.

5. **Whimsy corpus is a flat list of strings** (not `[word, 1]` weight pairs as the brief implied). The build_name_corpus.py script produced uniform weights, so `random.choice()` was used instead of `random.choices()` with weights.

---

## What The Reviewer Should Check

1. **Model type for secret attributes:** confirm REAL float [0,1] vs SmallInteger 1–100 is the intended design for the sim engine.

2. **Jersey range conventions:** verify the ranges used are acceptable or if specific rules should be enforced (e.g., do WRs really share 1–19 with QBs in this universe?).

3. **Position distribution totals match spec groups:** the 85-player template is built from the brief's group counts; verify the "Reserve/Walk-on (10)" positions are reasonable.

4. **SBC southern name corpus:** confirm players seeded for programs with `conglomerate_code = 'SBC'` (IDs 27–52) use the southern first-name pool (code does this via `is_sbc` flag).

5. **Re-seed idempotency:** the script uses `TRUNCATE TABLE players RESTART IDENTITY` before insert, so re-running with the same `--seed 42` produces identical output. This is the intended behavior.

6. **Migration chain:** `36a6ee9b555e` is now between `a1b2c3d4e5f6` (games) and `b2c3d4e5f6a7` (staff) in the chain. Verify this ordering is correct for the staff schema's dependencies.

---

## Handoff

Reviewer: run the following to verify independently:

```bash
# Verify counts
uv run python -c "
import sqlalchemy as sa; from sqlalchemy import create_engine, text
e = create_engine('postgresql+psycopg2://gridiron:gridiron@localhost:5438/gridiron')
with e.connect() as c:
    print('players:', c.execute(text('SELECT COUNT(*) FROM players')).scalar())
    print('programs_with_85:', c.execute(text('SELECT COUNT(*) FROM (SELECT program_id FROM players GROUP BY program_id HAVING COUNT(*)=85) x')).scalar())
"

# Dry-run re-seed check (should not error)
uv run seed-roster --db-url postgresql+psycopg2://gridiron:gridiron@localhost:5438/gridiron --seed 42 --dry-run
```
