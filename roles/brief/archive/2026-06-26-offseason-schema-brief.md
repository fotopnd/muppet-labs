# Brief: offseason-schema

**Role:** brief
**Sprint unit:** 01
**Project:** gridiron
**Date:** 2026-06-26

---

## Context

The off-season engine needs new schema primitives:
- Players need `class_year` (eligibility year 1–5) and `injury_status` for graduation/development logic
- Programs need `recruiting_states` (geographic territory) for recruiting score computation
- Coaches need `focus_states` (recruiter geographic focus) for recruiting score computation
- A `prospects` table holds the pre-generated recruit pool for each season
- A `portal_entries` table tracks players who enter the transfer portal

None of these tables exist yet.

---

## Objective

Single Alembic migration: add columns to `players`, `programs`, `coaches`; create `prospects` and `portal_entries` tables.

---

## Specification

**New migration file:** `alembic/versions/f7a8b9c0d1e2_offseason_schema.py`
- `revision = 'f7a8b9c0d1e2'`
- `down_revision = 'e6f7a8b9c0d1'`

### upgrade()

```python
def upgrade() -> None:
    # --- players ---
    op.add_column('players', sa.Column('class_year', sa.SmallInteger(), nullable=True))
    # Backfill: realistic distribution across 4 active years (year 5 is a redshirt holdover)
    # Target: ~25% yr1, ~25% yr2, ~25% yr3, ~20% yr4, ~5% yr5
    op.execute("""
        UPDATE players SET class_year = CASE
            WHEN random() < 0.25 THEN 1
            WHEN random() < 0.50 THEN 2
            WHEN random() < 0.75 THEN 3
            WHEN random() < 0.95 THEN 4
            ELSE 5
        END
    """)
    op.alter_column('players', 'class_year', nullable=False)

    op.add_column('players', sa.Column(
        'injury_status', sa.Text(), nullable=False, server_default='healthy'
    ))

    # --- programs ---
    op.add_column('programs', sa.Column(
        'recruiting_states', postgresql.ARRAY(sa.Text()), nullable=False,
        server_default='{}'
    ))

    # --- coaches ---
    op.add_column('coaches', sa.Column(
        'focus_states', postgresql.ARRAY(sa.Text()), nullable=False,
        server_default='{}'
    ))

    # --- prospects ---
    op.create_table(
        'prospects',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('sim_run_id', sa.Integer(),
                  sa.ForeignKey('sim_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('season_number', sa.SmallInteger(), nullable=False),
        sa.Column('first_name', sa.Text(), nullable=False),
        sa.Column('last_name', sa.Text(), nullable=False),
        sa.Column('position', sa.Text(), nullable=False),
        sa.Column('home_state', sa.Text(), nullable=False),
        sa.Column('rating', sa.SmallInteger(), nullable=False),   # 1–100 skill ceiling
        sa.Column('prestige', sa.SmallInteger(), nullable=False), # 1–5 star rating
        sa.Column('status', sa.Text(), nullable=False, server_default='available'),
        # available | committed | signed | no_offer
        sa.Column('committed_program_id', sa.Integer(),
                  sa.ForeignKey('programs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_prospects_sim_run_season', 'prospects',
                    ['sim_run_id', 'season_number'])

    # --- portal_entries ---
    op.create_table(
        'portal_entries',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('sim_run_id', sa.Integer(),
                  sa.ForeignKey('sim_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('season_number', sa.SmallInteger(), nullable=False),
        sa.Column('player_id', sa.Integer(),
                  sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        # playing_time | development | record | random
        sa.Column('status', sa.Text(), nullable=False, server_default='open'),
        # open | transferred | stayed | no_offer
        sa.Column('entered_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index('ix_portal_entries_sim_run_season', 'portal_entries',
                    ['sim_run_id', 'season_number'])
```

### downgrade()

```python
def downgrade() -> None:
    op.drop_table('portal_entries')
    op.drop_table('prospects')
    op.drop_column('coaches', 'focus_states')
    op.drop_column('programs', 'recruiting_states')
    op.drop_column('players', 'injury_status')
    op.drop_column('players', 'class_year')
```

### Import note

`from alembic import op` and `import sqlalchemy as sa` are already standard. Add:
```python
from sqlalchemy.dialects import postgresql
```

---

## Notes

- `class_year` backfill uses a single `UPDATE` with `random()` applied per-row. The cumulative-probability form (`random() < 0.25`, `random() < 0.50`, …) is correct because `random()` is evaluated fresh for each CASE branch per row in PostgreSQL.
- `injury_status` defaults `'healthy'` via `server_default`; existing rows pick it up automatically — no backfill needed.
- `recruiting_states` and `focus_states` are `TEXT[]` with empty-array default. Seeding realistic state lists is deferred to a separate script or future sprint.
- `prospects.status` values: `available` (not yet committed), `committed` (soft commitment, can be flipped), `signed` (NLI signed, permanent), `no_offer` (no school matched — rare).
- `portal_entries.reason` values: `playing_time`, `development`, `record`, `random`.
- Do NOT add `season` column to `players` — class progression is handled by incrementing `class_year` during the off-season engine run, not by a static season tag.

---

## Out of Scope

- No engine code this unit
- No API endpoints this unit
- No seeding of `recruiting_states` / `focus_states` with actual data

---

## Verification

```bash
uv run alembic upgrade head

uv run python3 -c "
import asyncio
from gridiron.database import engine
from sqlalchemy import text

async def main():
    async with engine.begin() as conn:
        # class_year distribution
        r = await conn.execute(text('''
            SELECT class_year, COUNT(*) AS cnt
            FROM players GROUP BY class_year ORDER BY class_year
        '''))
        for row in r.mappings():
            print(dict(row))

        # tables exist
        for t in ('prospects', 'portal_entries'):
            r = await conn.execute(text(f'SELECT COUNT(*) FROM {t}'))
            print(f'{t} row count:', r.scalar())

asyncio.run(main())
"
```

Expected: class_year 1–5 all present, rough 25/25/25/20/5 distribution. prospects and portal_entries both exist with 0 rows.

---

## Handoff

Commit message: `feat: offseason schema — class_year, injury_status, prospects, portal_entries`
Next units: 02 (prospect-generation) and 03 (offseason-api-stubs) both depend on this migration.
