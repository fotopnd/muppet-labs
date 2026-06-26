# Brief: sim-runs-migration

**Role:** brief
**Sprint unit:** 01
**Project:** gridiron
**Date:** 2026-06-26

---

## Context

All game queries currently hardcode `season = 1`. We need a `sim_runs` table so each execution of the simulation engine is tracked and can be promoted to production or discarded. Pruning a sim run must cascade cleanly through games → play_log and player_game_stats.

---

## Objective

Create the `sim_runs` table, add `games.sim_run_id` FK with cascade, backfill existing data, and add ON DELETE CASCADE to the two existing game-child FKs.

---

## Specification

**New migration file:** `alembic/versions/e6f7a8b9c0d1_sim_runs.py`
- `revision = 'e6f7a8b9c0d1'`
- `down_revision = 'd5e6f7a8b9c0'`

### upgrade()

```python
def upgrade() -> None:
    # 1. sim_runs table
    op.create_table(
        'sim_runs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('label', sa.Text(), nullable=False, server_default='alpha'),
        sa.Column('season_number', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('production_id', sa.Integer(), nullable=True),
        sa.Column('production_name', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default='running'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.UniqueConstraint('production_id', name='uq_sim_runs_production_id'),
    )

    # 2. Seed run 1 for existing data
    op.execute("INSERT INTO sim_runs (id, label, season_number, status) VALUES (1, 'alpha-001', 1, 'complete')")

    # 3. Add sim_run_id to games (nullable first for backfill)
    op.add_column('games', sa.Column('sim_run_id', sa.Integer(), nullable=True))
    op.execute("UPDATE games SET sim_run_id = 1")
    op.alter_column('games', 'sim_run_id', nullable=False)
    op.create_foreign_key(
        'fk_games_sim_run_id', 'games', 'sim_runs',
        ['sim_run_id'], ['id'], ondelete='CASCADE'
    )
    op.create_index('ix_games_sim_run_id', 'games', ['sim_run_id'])

    # 4. Add ON DELETE CASCADE to play_log.game_id
    op.drop_constraint('play_log_game_id_fkey', 'play_log', type_='foreignkey')
    op.create_foreign_key(
        'play_log_game_id_fkey', 'play_log', 'games',
        ['game_id'], ['id'], ondelete='CASCADE'
    )

    # 5. Add ON DELETE CASCADE to player_game_stats.game_id
    op.drop_constraint('player_game_stats_game_id_fkey', 'player_game_stats', type_='foreignkey')
    op.create_foreign_key(
        'player_game_stats_game_id_fkey', 'player_game_stats', 'games',
        ['game_id'], ['id'], ondelete='CASCADE'
    )
```

### downgrade()

```python
def downgrade() -> None:
    op.drop_constraint('player_game_stats_game_id_fkey', 'player_game_stats', type_='foreignkey')
    op.create_foreign_key('player_game_stats_game_id_fkey', 'player_game_stats', 'games', ['game_id'], ['id'])
    op.drop_constraint('play_log_game_id_fkey', 'play_log', type_='foreignkey')
    op.create_foreign_key('play_log_game_id_fkey', 'play_log', 'games', ['game_id'], ['id'])
    op.drop_index('ix_games_sim_run_id', table_name='games')
    op.drop_constraint('fk_games_sim_run_id', 'games', type_='foreignkey')
    op.drop_column('games', 'sim_run_id')
    op.drop_table('sim_runs')
```

---

## Notes

- FK constraint names for play_log and player_game_stats may differ from the defaults above. If `op.drop_constraint` fails with "constraint not found", query `information_schema.table_constraints` to find the real names:
  ```sql
  SELECT constraint_name FROM information_schema.table_constraints
  WHERE table_name IN ('play_log', 'player_game_stats') AND constraint_type = 'FOREIGN KEY';
  ```
- `games.season` stays — it is the in-universe year number and is used by the coaches CTE to group season history. Do not remove it.

---

## Out of Scope

- Do not touch any API routers or engine files — those are units 02 and 03
- Do not add a `/sim-runs` API endpoint — unit 03

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
        # sim_runs row exists
        r = await conn.execute(text('SELECT * FROM sim_runs'))
        print('sim_runs:', [dict(row) for row in r.mappings()])

        # all games have sim_run_id = 1
        r = await conn.execute(text('SELECT COUNT(*) FROM games WHERE sim_run_id = 1'))
        print('games with sim_run_id=1:', r.scalar())

        r = await conn.execute(text('SELECT COUNT(*) FROM games WHERE sim_run_id IS NULL'))
        print('games with NULL sim_run_id (should be 0):', r.scalar())

asyncio.run(main())
"
```

Expected: 1 sim_run row (id=1, label='alpha-001'), all existing games have sim_run_id=1, no NULLs.

---

## Handoff

Commit message: `feat: sim_runs table + games.sim_run_id + cascade FKs`
Next unit: 02 (sim-runs-engine) depends on this migration being applied.
