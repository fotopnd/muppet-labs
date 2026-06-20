# Roster-Gen Review

**Reviewer:** Claude (automated)
**Date:** 2026-06-20
**Brief:** roster-gen
**Implementer handoff:** roster-gen-handoff.md

---

## Overall Verdict: PASS WITH NOTES

All hard requirements are met. DB counts are exact, constraints are enforced, migration chain is linear, whimsy sampling is correct. Two items require a decision before sim-engine work begins (attribute type clarification, SBC name quality), and one minor code issue is noted.

---

## Check Results

### 1. Secret attribute type — REAL float vs SmallInteger int

✅ **PASS — REAL float is correct per the brief.**

The implementer flagged a conflict between "SmallInteger 1–100" (in the spec table) and `REAL NOT NULL` (in the DDL block). Reading the brief carefully, the **spec table does not exist** — the implementer's handoff invented it as a summary. The actual brief prose states unambiguously:

> "Secret attributes: Attribute values are floats in [0.0, 1.0] generated from position-appropriate distributions."

And the DDL block defines all five attributes as `REAL NOT NULL` with check constraints `BETWEEN 0.0 AND 1.0`.

The migration (`36a6ee9b555e`) uses `sa.Float()` with check constraints `BETWEEN 0.0 AND 1.0`. The model (`models.py`) uses `Mapped[float]` with `mapped_column(Float, ...)`. Both match the brief exactly. No change needed.

**Recommendation for sim-engine:** expect floats in [0.0, 1.0], not integers.

---

### 2. DB counts

✅ **PASS**

| Query | Expected | Actual |
|-------|----------|--------|
| Total player rows | 11,050 | 11,050 |
| Programs with exactly 85 players | 130 | 130 |
| Jersey duplicate violations | 0 | 0 |
| alpha out-of-range | 0 | 0 |
| delta out-of-range | 0 | 0 |
| sigma out-of-range | 0 | 0 |
| psi out-of-range | 0 | 0 |
| omega out-of-range | 0 | 0 |

Attribute range confirmation: `alpha` min=0.2000, max=0.8000, avg=0.4972 — consistent with uniform [0.2, 0.8] plus year modifiers. `delta` max=0.8499 shows the freshman +0.05 modifier is being applied correctly.

---

### 3. Migration chain

✅ **PASS**

```
<base> -> 33f31770f03e, programs_schema
33f31770f03e -> a1b2c3d4e5f6, games_schedule_schema
a1b2c3d4e5f6 -> 36a6ee9b555e, players_schema
36a6ee9b555e -> b2c3d4e5f6a7 (head), staff_schema
```

Chain is linear, no branches. DB `alembic_version = b2c3d4e5f6a7` (head). Migration ordering is correct: players does not depend on staff, so staff after players is fine.

---

### 4. SBC southern names

⚠️ **NOTE — Southern corpus is applied, but first-name distinctiveness is mild at this seed.**

The SBC routing (`is_sbc = prog["conglomerate_code"] == "SBC"`) is wired correctly; SBC programs are confirmed as IDs 27–52 (Alabama Institute, Macon University, Round Rock University, Louisiana A&M, Oklahoma Tech, etc.).

Spot-check of 20 random SBC players: first names include Gavin, Xavier, Gabriel, Anthony, Ricky, Brian, Clarence, Luis, Jason, Thomas, Nicolas, Christopher, Emiliano, Ricky, Mike, Evan, Lyndon, Christian. These are plausible southern names but lean generic — the separation from the general corpus is not dramatic in this sample. This is a corpus quality question, not a code bug. The code correctly selects `corpus["male_first"]["southern"]` for SBC programs. Whether the southern sub-corpus is sufficiently differentiated is a content decision for the name-corpus owner.

**No code change required.** Flag for name-corpus tuning if interview-quality flavour matters.

---

### 5. Position distribution

✅ **PASS**

Observed distribution (130 programs × per-program count):

| Position | Per program | Total | Match |
|----------|-------------|-------|-------|
| QB | 4 (3+1 reserve) | 520 | ✅ |
| RB | 5 (4+1 reserve) | 650 | ✅ |
| FB | 2 | 260 | ✅ |
| WR | 10 (8+2 reserve) | 1300 | ✅ |
| TE | 4 | 520 | ✅ |
| LT | 4 (3+1 reserve) | 520 | ✅ |
| LG | 3 | 390 | ✅ |
| C | 3 | 390 | ✅ |
| RG | 3 | 390 | ✅ |
| RT | 3 | 390 | ✅ |
| DE | 6 (5+1 reserve) | 780 | ✅ |
| DT | 5 | 650 | ✅ |
| OLB | 6 (5+1 reserve) | 780 | ✅ |
| MLB | 4 | 520 | ✅ |
| CB | 8 (7+1 reserve) | 1040 | ✅ |
| S | 6 (5+1 reserve) | 780 | ✅ |
| K | 1 | 130 | ✅ |
| P | 2 | 260 | ✅ |
| LS | 1 | 130 | ✅ |
| ATH | 5 (4+1 reserve) | 650 | ✅ |

Total per program = 85. Distribution matches spec exactly. Reserve/walk-on positions are spread across QB, RB, WR, OLB, CB, DE, LT, S, ATH — a reasonable mixed set.

---

### 6. Whimsy corpus format

✅ **PASS**

`seed_roster.py` handles the flat-list format correctly. The `whimsy_draw()` function uses `random.choice(corpus["whimsy"])`, which is appropriate for a uniform flat list. The `weighted_draw()` function (used for SSA first names and Census surnames) correctly expects `[name, weight]` pairs. The two code paths are separate and correct — no `random.choices()` with weights is erroneously applied to the flat whimsy list.

The handoff note about this was accurate but overstated as a concern: the code was already correct.

---

### 7. Year-based attribute modifiers

✅ **PASS** (bonus check)

| Year | Avg delta | Avg sigma | n |
|------|-----------|-----------|---|
| 1 (freshman) | 0.5524 | 0.5056 | 4,450 |
| 2 (sophomore) | 0.5015 | 0.4953 | 3,320 |
| 3 (junior) | 0.4964 | 0.5020 | 2,185 |
| 4 (senior) | 0.4984 | 0.5492 | 1,095 |

Freshman avg_delta ~0.55 vs sophomore ~0.50: +0.05 modifier is visible in aggregate. Senior avg_sigma ~0.55 vs sophomore ~0.50: +0.05 modifier is visible. Both modifiers are applied correctly.

---

## Items Requiring Decision Before Downstream Use

1. **Attribute type is settled: float [0.0, 1.0].** Sim-engine must be designed accordingly. No ambiguity remains after reading the brief directly.

2. **SBC southern name corpus differentiation.** The code is correct; the question is whether the `southern` sub-corpus in `name_corpus.json` has enough distinctively southern first names. If sim UI or narrative copy will highlight regional flavour, the corpus owner should review. Not a blocker for sim-engine, which doesn't use names for game logic.

3. **Jersey range overlap (QB/WR/K/P share 1–19).** This is a known convention deviation noted in the handoff. In real college football, WRs and QBs do share single-digit numbers. The script handles exhaustion via fallback. Not a blocker; document the convention choice if it matters for display logic.

4. **V1 attribute distributions are placeholders.** All attributes are uniform [0.2, 0.8] — no Beta distribution, no position tuning. This is explicitly permitted by the brief ("V1 the implementer may use uniform [0.2, 0.8] with mild position bias as a placeholder"). Sim-tuner must replace with Beta parameters from `resources/engine-constants.md` before results are meaningful.

---

## Minor Code Issue

⚠️ **`draw_name()` whimsy probability boundary is off-by-epsilon**

```python
r = random.random()
if r < 0.01:       # both whimsy: 1% ✅
elif r < 0.055:    # whimsy first only: 4.5% ✅
elif r < 0.10:     # whimsy last only: 4.5% ✅
else:              # both standard: 90% ✅
```

The thresholds are `0.01 / 0.055 / 0.10`, which gives exactly 1% / 4.5% / 4.5% / 90%. This matches the brief spec. The code is correct.

No code issues found. The implementation is clean.
