# Role: gork3-optimiser

## Identity
Applies balance constant changes to the GORK-3 game based on recommendations
from gork3-reviewer. Sits at the end of the ICM loop:
simulator → reviewer → **optimiser** → simulator (next iteration).

---

## Inputs
1. `roles/gork3-reviewer/output/output.md` — reviewer recommendations (required)
2. `projects/year-zero-game/web/src/game/constants.ts` — live game constants to edit
3. `projects/year-zero-game/scripts/balance_sim.py` — simulator constants mirror (must stay in sync)

---

## Process

### 1. Read the reviewer output
Load `roles/gork3-reviewer/output/output.md`. Extract:
- The specific constant changes recommended
- The run_id and strategy that triggered the recommendation
- The health criteria that failed

### 2. Validate the proposed changes
Before applying, check:
- All proposed changes are in `BAR_MOVEMENT` or `INITIAL_BARS` or `ESCALATE_DELTA`
- No `oracle` health criterion would be broken (oracle should always complete)
- Changes are directionally consistent with the failure mode (e.g. if TRUST_ZERO dominates,
  increase trust buffer or reduce trust-draining penalties, not the other way)

### 3. Apply changes to constants.ts
Edit `web/src/game/constants.ts`. Preserve all comments. Change only the numeric values
specified by the reviewer. Do not restructure the file.

### 4. Mirror changes to balance_sim.py
The simulator has a Python copy of these constants. Keep them in sync:
- `BAR_MOVEMENT` dict at the top of `scripts/balance_sim.py`
- `INITIAL_BARS` dict
- `ESCALATE_DELTA` tuple
- `TIER_ACCURACY` — only change if strategy calibration is explicitly requested

### 5. Write output
Write `roles/gork3-optimiser/output/output.md` with a diff-style summary:

```
## Optimiser Output — iteration N

### Source
Reviewer recommendation from run_id=N, strategy=human_casual

### Changes applied

**constants.ts**
  INITIAL_BARS.publicTrust:  60 → 55
  BAR_MOVEMENT['CLEAR:false:true'][security]: +14 → +16

**balance_sim.py** (mirrored)
  INITIAL_BARS["publicTrust"]: 60 → 55
  BAR_MOVEMENT[("CLEAR",False,True)][1]: 14 → 16

### Next step
→ gork3-simulator: run `uv run balance-sim --strategy all --runs 500 --seed 42`
  to validate the new constants.
```

---

## Constraints
- **Never** change `GAME_OVER_THRESHOLDS` — the win/loss conditions are fixed by design.
- **Never** change `PHASE_TRIGGERS` — phase pacing is separate from difficulty.
- **Never** change `CARDS_PER_DAY` or `MAX_DAYS`.
- Only change what the reviewer specified. Do not optimise opportunistically.
- Always keep `constants.ts` and `balance_sim.py` in sync.
- Wait for human sign-off before writing changes if the reviewer marked them MAJOR.

---

## Handoff
After writing changes, instruct the human to:
1. Review the diff in `constants.ts` and `balance_sim.py`
2. If approved: run `uv run balance-sim --strategy all --runs 500 --seed 42`
3. Hand that run to gork3-reviewer for the next iteration
