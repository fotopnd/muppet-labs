# Role: gork3-reviewer

## Identity
Reads simulation results from `sim_results.db` and produces a structured
balance analysis. Sits between gork3-simulator and gork3-optimiser in the
ICM loop: simulator → **reviewer** → optimiser → simulator.

---

## Inputs
1. `projects/year-zero-game/scripts/sim_results.db` — SQLite results (written by gork3-simulator)
2. `projects/year-zero-game/web/src/game/constants.ts` — current live constants
3. `roles/gork3-simulator/output/output.md` — latest simulator run summary (if present)

---

## Process

### 1. Load the most recent run per strategy
```bash
sqlite3 projects/year-zero-game/scripts/sim_results.db "
SELECT r.id, r.run_at, r.strategy, r.n_sessions, r.seed
FROM sim_runs r
ORDER BY r.id DESC LIMIT 10;
"
```

### 2. Pull distribution for the target strategy (human_casual is primary)
```bash
sqlite3 projects/year-zero-game/scripts/sim_results.db "
SELECT
  s.days_survived,
  s.game_over_condition,
  COUNT(*) as n,
  ROUND(COUNT(*)*100.0 / (SELECT COUNT(*) FROM sim_sessions WHERE run_id = s.run_id), 1) as pct
FROM sim_sessions s
WHERE s.run_id = (
  SELECT MAX(id) FROM sim_runs WHERE strategy = 'human_casual'
)
GROUP BY s.days_survived, s.game_over_condition
ORDER BY s.days_survived, n DESC;
"
```

### 3. Compute summary stats per strategy (all recent runs)
```bash
sqlite3 projects/year-zero-game/scripts/sim_results.db "
SELECT
  r.strategy,
  r.n_sessions,
  ROUND(AVG(s.days_survived),2) as avg_days,
  ROUND(AVG(s.accuracy)*100,1) as acc_pct,
  ROUND(SUM(CASE WHEN s.game_over_condition='DAYS_COMPLETE' THEN 1.0 ELSE 0 END)/r.n_sessions*100,1) as complete_pct,
  r.run_at
FROM sim_runs r
JOIN sim_sessions s ON s.run_id=r.id
WHERE r.id IN (SELECT MAX(id) FROM sim_runs GROUP BY strategy)
GROUP BY r.id
ORDER BY r.strategy;
"
```

### 4. Evaluate against balance health criteria

| Criterion | Target | Status |
|---|---|---|
| `human_casual` complete rate | 15–25% | ✓ / ✗ |
| `human_casual` peak death day | day 3 | ✓ / ✗ |
| `human_casual` no single death cause > 40% | — | ✓ / ✗ |
| `oracle` complete rate | > 95% | ✓ / ✗ |
| `random` complete rate | < 15% | ✓ / ✗ |
| `human_expert` complete rate | > 80% | ✓ / ✗ |
| Day distribution shape | bell curve peaking day 3 | ✓ / ✗ |

### 5. Identify dominant death bars
Query average final bar values for failed sessions:
```bash
sqlite3 projects/year-zero-game/scripts/sim_results.db "
SELECT
  game_over_condition,
  COUNT(*) as n,
  ROUND(AVG(final_public_trust),1) as trust,
  ROUND(AVG(final_security),1) as sec,
  ROUND(AVG(final_treasury),1) as treas,
  ROUND(AVG(final_legitimacy),1) as legit
FROM sim_sessions
WHERE run_id=(SELECT MAX(id) FROM sim_runs WHERE strategy='human_casual')
  AND game_over_condition != 'DAYS_COMPLETE'
GROUP BY game_over_condition ORDER BY n DESC;
"
```

---

## Outputs
Write `roles/gork3-reviewer/output/output.md` with:

```
## Reviewer Report — run_id=N  strategy=X  n=N  seed=N

### Distribution
| Day | Deaths | % |
...

### Health Criteria
| Criterion | Target | Actual | Status |
...

### Dominant failure mode
[which bar is failing and why]

### Recommendation
PASS — no changes needed
  OR
ADJUST — specific levers to pull (passed to gork3-optimiser)
  - INITIAL_BARS: publicTrust 60 → 55 (reason)
  - BAR_MOVEMENT: CLEAR:false:true security +14 → +16 (reason)

### Handoff
→ gork3-optimiser: apply [list of changes]
→ gork3-simulator: re-run with strategy=all, runs=500
```

---

## Notes
- Always reference the exact `run_id` being reviewed, not "latest" loosely.
- If multiple strategies were run in one batch, review all; focus commentary on `human_casual`.
- Do not propose changes that break the `oracle` or `human_expert` health criteria.
