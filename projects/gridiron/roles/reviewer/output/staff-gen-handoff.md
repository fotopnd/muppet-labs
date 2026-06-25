# Staff-Gen Handoff — Reviewer

**Feature:** staff-gen  
**Session date:** 2026-06-20  
**Implementer:** Claude (automated)  
**Next role:** reviewer  

---

## What Was Built

### New files

| File | Purpose |
|------|---------|
| `/Users/fotopnd/Documents/muppet-labs/projects/gridiron/scripts/seed_staff.py` | Seed script — generates and inserts coaches + boosters for all 130 programs |
| `/Users/fotopnd/Documents/muppet-labs/projects/gridiron/alembic/versions/b2c3d4e5f6a7_staff_schema.py` | Alembic migration creating `coaches` and `boosters` tables |

### Modified files

| File | Change |
|------|--------|
| `/Users/fotopnd/Documents/muppet-labs/projects/gridiron/gridiron/models.py` | Added `Coach` and `Booster` SQLAlchemy models + `Program.coaches` / `Program.boosters` back-references |
| `/Users/fotopnd/Documents/muppet-labs/projects/gridiron/pyproject.toml` | Added `seed-staff = "scripts.seed_staff:main"` entrypoint |

---

## Actual Row Counts (seed=42)

| Table | Rows | Expected |
|-------|------|----------|
| coaches | 650 | 650 (5 x 130) |
| boosters | 534 | 390–650 |

Booster distribution: 25 programs got 3, 66 got 4, 39 got 5.

All DB validation checks passed:
- 650 coaches total
- Each program has exactly one coach per role (5 roles x 130 programs)
- All coach ratings in [0.0, 1.0]
- 534 boosters in valid range [390, 650]
- All programs have 3–5 boosters
- All influence values in [0.0, 1.0]

---

## Migration Details

Migration `b2c3d4e5f6a7_staff_schema.py` chains off `36a6ee9b555e` (players_schema), which itself chains off `a1b2c3d4e5f6` (games_schedule_schema). The migration creates:
- `coaches` table with CHECK constraint on `rating BETWEEN 0.0 AND 1.0`, index on `program_id`
- `boosters` table with CHECK constraint on `influence BETWEEN 0.0 AND 1.0`, index on `program_id`

Migration was applied successfully: `uv run alembic upgrade head`

---

## Deviations from Brief

1. **Coach gender**: The brief does not specify gender for coaches. The implementation samples `male_first` and `female_first` with equal 50% probability (same as the spirit of the brief). The brief only specifies "older-sounding names" for head coaches but does NOT provide a separate SSA corpus filtered to 1960–1975. This was not feasible with the existing corpus which contains weighted modern counts. **Head coaches use the same pool as other coaches.** The brief says "if feasible; otherwise use general pool" — so this is within spec.

2. **Whimsy corpus format**: The brief states whimsy is `[[word, 1], ...]` but the actual corpus is a flat `[word, ...]` list. The seed script handles the flat format correctly (uses `random.choice()` instead of weighted sampling).

3. **Idempotency**: The script uses `DELETE FROM boosters / DELETE FROM coaches` before re-inserting, making it safe to re-run. The brief does not specify idempotency behavior, but this is consistent with the seed_programs.py pattern of using `ON CONFLICT DO UPDATE`.

4. **Booster "old-money" surname bias**: Implemented by filtering the surname pool to entries with `len(surname) <= 8` before sampling. This reduces the pool from 24,889 to 21,837 surnames but retains weighted sampling from that subset.

---

## What the Reviewer Should Check

1. **Model correctness**: Verify `Coach` and `Booster` models in `gridiron/models.py` match the brief schema and the migration DDL.

2. **Whimsy rule application**: Confirm the 10%/1% rates match roster-gen's implementation (if it exists) for consistency. Check `generate_name()` in `seed_staff.py`.

3. **Southern corpus split**: SBC (`conglomerate_id=2`) uses `corpus['male_first']['southern']` / `corpus['female_first']['southern']` for first names. Other conglomerates use `'general'`. Verify this matches the intended brief behavior.

4. **Idempotency**: Run the seed script twice and confirm counts remain at 650 / 534 (second run should clear and re-insert).

5. **CLI invocation**: Test both invocation forms:
   ```
   uv run scripts/seed_staff.py --db-url postgresql+asyncpg://gridiron:gridiron@localhost:5438/gridiron --seed 42 --dry-run
   uv run seed-staff --seed 42
   ```

6. **Migration chain**: Verify `uv run alembic history` shows a clean linear chain ending at `b2c3d4e5f6a7`.

7. **Head coach name quality**: Sample a few head coaches from each conglomerate to confirm southern-flavored names appear in SBC programs.

---

## Handoff

Ready for reviewer. No blockers. The staff-gen feature is complete and validated. The tables are live in the DB with 650 coaches and 534 boosters. Next step after review would be wiring coach/booster data into team profile API endpoints (blocked on API design — not in this brief).
