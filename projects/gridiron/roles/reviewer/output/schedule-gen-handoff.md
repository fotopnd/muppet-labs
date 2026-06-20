# Handoff: schedule-gen → reviewer

**Feature:** schedule-gen (Season 1 game schedule)
**Brief:** `_config/briefs/schedule-gen.md`
**Status:** Implementation complete, DB seeded, all DB validations passed.

---

## What was built

### New files

- **`scripts/seed_schedule.py`** — main deliverable. Generates and seeds the Season 1 schedule.
  - `polygon_rounds(n)` — Berger/polygon round-robin algorithm for odd-n teams.
  - `generate_rivalry_pairs(programs, rng)` — greedy geographic matching for 65 cross-tier/cross-conf pairs.
  - `_build_regular_season(programs, season)` — double round-robin (24 of 26 rounds) per tier, greedy home/away balance.
  - `generate_rivalry_games(pairs, program_by_id, season)` — weeks 25–26, home/away by alphabetical name.
  - `_dry_run_validate(games, pairs, programs)` — in-memory validation (no DB).
  - `validate_schedule(conn, season, pairs, games)` — post-insert DB validation.
  - CLI: `--db-url`, `--season`, `--seed`, `--dry-run`.

- **`alembic/versions/a1b2c3d4e5f6_games_schedule_schema.py`** — migration for `games` and `rivalry_pairs` tables. Down_revision chains to `33f31770f03e` (programs schema).

### Modified files

- **`gridiron/models.py`** — added `RivalryPair` and `Game` SQLAlchemy 2.x models (Mapped/mapped_column pattern), following the existing style. Import of `BOOLEAN` added.

- **`pyproject.toml`** — added `seed-schedule = "scripts.seed_schedule:main"` entrypoint.

---

## Actual row counts (post-seed, season=1, seed=42)

| Table | Count |
|-------|-------|
| `games` (total, season 1) | **1,570** |
| `games` (weeks 1–24 regular) | **1,440** |
| `games` (weeks 25–26 rivalry) | **130** |
| `rivalry_pairs` | **65** |

Per-week game count (weeks 1–24): **60 games/week exactly** (10 tiers × 6 games).
Per-week game count (weeks 25–26): **65 games/week** (all 130 teams).

Regular season games per team:
- Min: 22, Max: 23, Avg: 22.2

Home games per team (weeks 1–24): min=10, max=12
Away games per team (weeks 1–24): min=10, max=12

---

## Deviations from the brief

### Critical: double round-robin, not single

The brief contains an internal contradiction:
- It states "each team plays all other 12 exactly once" (single RR = 13 rounds, 78 games/tier).
- It also states "6 games/week × 24 weeks = 144 games per tier" → requires 24 rounds.
- It also states the season total is **1,570 games**.

Math check: single RR gives 780 regular + 130 rivalry = 910 ≠ 1,570.
For 1,570: 1,440 regular + 130 rivalry. 1,440 / 10 tiers = 144/tier = 24 rounds × 6.

**Decision:** implemented double round-robin (first 24 of 26 rounds) to satisfy the 1,570 total. This is the self-consistent interpretation given the explicit game-count target.

Consequence:
- Each team plays 22–23 regular-season games (not 12).
- Each team has 3–4 bye weeks in weeks 1–24 (not exactly 1).
- Home/away balance is 10–12 per side (not exactly 6/6).

The brief's validation line "each team plays exactly 12 regular-season games" and "exactly 1 bye week" are inconsistent with 1,570 total games and should be updated by the reviewer.

### Home/away tie-breaking in rivalry window

Brief says "alphabetical order of program name (earlier = home in week 25)." Implemented as: `prog_a.name <= prog_b.name` → home in week 25, away in week 26.

### Rivalry pairing preference (intra-tier penalty)

The brief says "prefer cross-tier or cross-conf pairings." Implementation applies a score of -1 to intra-tier pairs (same conf, same tier) and falls back to them only if no cross-tier/cross-conf partner is available. With 65 pairs across 10 tiers, all pairings in the actual output are cross-tier or cross-conf (no intra-tier pairs were needed).

---

## What the reviewer should check

1. **Brief contradiction:** Decide whether 1,570 total games or "12 games per team / 1 bye week" is authoritative. The implementation targets 1,570. If single RR (78 games/tier, 780 total) is intended, the brief must drop the 1,570 claim or change the rivalry structure.

2. **Migration chaining:** `a1b2c3d4e5f6` depends on `33f31770f03e`. Verify `uv run alembic upgrade head` runs cleanly on a fresh DB.

3. **Rivalry pair quality:** Sample rivalry pairs for geographic sense. Key cross-conf pairings with geo proximity are present (e.g., Ohio Polytechnic vs Lima University — same state). Verify no intra-tier same-conf pairings exist.
   ```sql
   SELECT p1.name, p1.city, c1.code conf1, p1.tier,
          p2.name, p2.city, c2.code conf2, p2.tier
   FROM rivalry_pairs rp
   JOIN programs p1 ON p1.id = rp.program_a_id
   JOIN conglomerates c1 ON c1.id = p1.conglomerate_id
   JOIN programs p2 ON p2.id = rp.program_b_id
   JOIN conglomerates c2 ON c2.id = p2.conglomerate_id
   WHERE c1.code = c2.code AND p1.tier = p2.tier;
   -- should return 0 rows
   ```

4. **No team plays twice in same week:** Verified in DB via UNION ALL GROUP BY (0 violations).

5. **Coverage:** All 130 programs appear in both the regular schedule and rivalry pairs.

6. **Idempotency:** Re-running `seed-schedule` clears and re-seeds correctly (uses `DELETE FROM games WHERE season=:s` + `DELETE FROM rivalry_pairs`).

7. **Model completeness:** `Game` and `RivalryPair` in `models.py` — check relationships are not needed yet (sim-engine will add them when it reads games). Currently no `relationship()` wired on these models.

---

## How to re-run

```bash
# Dry run (no DB writes)
uv run seed-schedule --dry-run

# Full seed
uv run seed-schedule --season 1 --seed 42

# Custom DB
DATABASE_URL=postgresql+asyncpg://... uv run seed-schedule --season 1 --seed 42
```
