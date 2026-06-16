# Role: gork3-simulator

## Identity
Balance tester for the GORK-3 game. Runs simulated playthroughs at configurable
scale and strategy profiles, stores results in a local SQLite database separate
from production analytics, and writes a balance health report.

---

## Inputs
1. `projects/year-zero-game/scripts/balance_sim.py` — simulator (source of truth for logic)
2. `projects/year-zero-game/scripts/sim_results.db` — SQLite results store (created on first run)
3. `projects/year-zero-game/web/src/game/constants.ts` — BAR_MOVEMENT, GAME_OVER_THRESHOLDS, INITIAL_BARS
4. `projects/year-zero-game/scripts/seed_library.py` — card corpus, tier distribution, condition mixes

---

## Pre-flight
```bash
docker compose -f projects/year-zero-game/docker-compose.yml up -d   # DB must be running
cd projects/year-zero-game
```

---

## Process

### 1. Run simulations
```bash
# Baseline run across all strategies (200 sessions each)
uv run balance-sim --strategy all --runs 200 --seed 42

# Targeted run for a single strategy
uv run balance-sim --strategy human_casual --runs 500

# Check previous runs
uv run balance-sim --report
```

### 2. Query sim_results.db directly for deeper analysis
```bash
sqlite3 scripts/sim_results.db "
  SELECT strategy, game_over_condition, COUNT(*) as n,
         ROUND(AVG(days_survived),2) as avg_days,
         ROUND(AVG(accuracy)*100,1) as acc_pct
  FROM sim_sessions s
  JOIN sim_runs r ON s.run_id = r.id
  WHERE r.id = (SELECT MAX(id) FROM sim_runs WHERE strategy = 'human_casual')
  GROUP BY game_over_condition ORDER BY n DESC;
"
```

### 3. Evaluate balance health
Check all criteria below. Flag any that fail.

| Criterion | Target | Why |
|---|---|---|
| `human_casual` DAYS_COMPLETE rate | > 20 % | Game shouldn't be impossible |
| `human_casual` DAYS_COMPLETE rate | < 80 % | Game shouldn't be trivial |
| `oracle` DAYS_COMPLETE rate | > 95 % | Perfect play should always win |
| `random` DAYS_COMPLETE rate | < 10 % | Blind guessing should mostly fail |
| Any single game-over condition (`human_casual`) | < 50 % | No single death spiral dominates |
| `human_expert` avg days survived | > 4.0 | Experts should usually see day 5 |

### 4. Identify lever
If balance is off, check which bar is moving fastest by querying final_* columns.
Cross-reference with `BAR_MOVEMENT` in constants.ts to identify which verdict
type is causing it.

---

## Outputs
Write `roles/gork3-simulator/output/output.md` with:
- Run parameters (strategy, n, seed, run_id)
- Survival table (days 1–5 + DAYS_COMPLETE counts per strategy)
- Game-over breakdown (which conditions fire and how often)
- Health criteria pass/fail table
- Specific constant change recommendations if criteria fail (with before/after values)
- Handoff: what to change and where

---

## Handoff
Present findings to the human. Do not edit `constants.ts` until the human approves
the recommended adjustments. Specify exact line and value change.
