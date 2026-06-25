# Role: gridiron-sim-tuner

## Identity

Sandbox QA role for the gridiron simulation engine. Runs the engine in complete
isolation from the production environment — no PostgreSQL, no SSE queues, no FastAPI.
All simulation output goes to an in-memory structure and an optional local SQLite file.

Purpose: validate engine balance, catch statistical anomalies, stress-test at scale,
and confirm that design-doc targets (score distributions, play frequencies, Elo
convergence, promotion/relegation churn, postseason Tier 2 representation) are met
before any code ships to production.

**Hard isolation contract:**
- Never imports `gridiron.database`, `gridiron.config`, or `gridiron.api`
- Never connects to PostgreSQL (port 5438 or any other)
- Never touches `app.state` or SSE infrastructure
- Reads from `gridiron.engine` only
- Writes only to `scripts/sandbox.db` (SQLite) and `roles/sim-tuner/output/output.md`

---

## Inputs

| Source | Path | Notes |
|--------|------|-------|
| Engine | `gridiron/engine/` | Simulation logic — must be implemented before this role can run |
| Constants | `resources/engine-constants.md` | Balance parameters; created when engine is built |
| Prior output | `roles/sim-tuner/output/output.md` | Read before running to track drift from last baseline |
| CLI args | — | See Process section |

---

## Pre-flight

```bash
# No docker required — sandbox uses SQLite only
cd projects/gridiron
uv run sim-sandbox --check   # confirms engine is importable; prints version
```

---

## Process

### 1. Confirm engine is importable

```bash
uv run sim-sandbox --check
```

If this fails, the engine is not yet implemented. Stop here and flag to implementer.

### 2. Run a baseline season

```bash
# Single season, all 130 teams, fixed seed
uv run sim-sandbox --seasons 1 --seed 42

# Multi-season stress test
uv run sim-sandbox --seasons 10 --seed 42

# High-volume scale test
uv run sim-sandbox --seasons 50 --seed 42 --quiet
```

### 3. Query sandbox.db for deeper analysis

```bash
sqlite3 scripts/sandbox.db "
  SELECT season, COUNT(*) as games,
         ROUND(AVG(home_score + away_score), 1) as avg_total_points,
         ROUND(AVG(ABS(home_score - away_score)), 1) as avg_margin
  FROM games
  GROUP BY season ORDER BY season;
"
```

### 4. Evaluate balance health

Check every criterion in the table below. Record PASS / FAIL / WARN per line.

| Criterion | Target | Source |
|-----------|--------|--------|
| Avg total points per game | 44–58 | Realistic college football range |
| Avg plays per game | 120–150 | Design doc §4.2 |
| Rush play % of non-ST plays | 40–50% | Realistic college football |
| Pass play % of non-ST plays | 50–60% | Realistic college football |
| Turnover rate per game | 2.0–3.5 | Combined INTs + fumbles |
| Upset rate (regular season) | 20–30% | Lower-Elo team wins |
| Upset rate (Rivalry Window) | 28–40% | Primetime Drama Multiplier active |
| Upset rate (postseason) | 28–40% | Primetime Drama Multiplier active |
| Tier 2 teams reaching QF or beyond per season | ≥ 1 | Cinderella path viable |
| Elo spread top-to-bottom after 3+ seasons | > 200 points | Stratification occurring |
| Teams relegated every season (per conglomerate) | Exactly 2 | Design spec |
| No team wins fewer than 2 games in a 24-game season | True | Prevents dead programs |
| avg plays per game std dev | < 20 | Consistent game length |

### 5. Identify lever

If any criterion fails, cross-reference with `resources/engine-constants.md` to find
the probability parameter responsible. Record the specific constant, current value,
proposed value, and expected effect.

---

## Output

Write `roles/sim-tuner/output/output.md` using the required structure below.
Archive the previous output to `roles/sim-tuner/archive/YYYY-MM-DD-output.md` first.

---

## Handoff

Present findings to the human. Do not edit engine constants until the human approves.
Specify exact constant name, file path, current value, and proposed value for each
recommended change.
