# Review: schedule-gen

**Reviewer:** Claude (reviewer role)
**Date:** 2026-06-20
**Feature:** Season 1 game schedule generation
**Brief:** `_config/briefs/schedule-gen.md`
**Handoff:** `roles/reviewer/output/schedule-gen-handoff.md`

---

## Overall Verdict: PASS WITH NOTES

The implementation is correct and internally consistent. All DB counts match the 1,570-game target. The one structural issue is a brief contradiction that was resolved by the implementer in the right direction — but the brief must be updated to remove the contradictory "12 games per team / 1 bye week" language. One minor design question is flagged on nullable program IDs in the Game model.

---

## Check Results

### 1. Brief Contradiction — 1,570 games vs "12 games per team"

**Finding: The brief contains an internal contradiction. The implementer resolved it correctly.**

The brief states both:
- "each team plays all other 12 exactly once" (single round-robin, 13 rounds)
- "6 games/week × 24 weeks = 144 games per tier" and total = **1,570 games**

These are mutually exclusive:
- Single RR: 78 games/tier × 10 tiers = 780 regular + 130 rivalry = **910 total** (not 1,570)
- Double RR (24 of 26 rounds): 144 games/tier × 10 tiers = 1,440 regular + 130 rivalry = **1,570 total** (matches)

The arithmetic inside the brief already uses double-RR numbers — "6 games/week × 24 weeks = 144" is only coherent if each team plays every opponent twice. The "12 games exactly once" and "1 bye week" language are copy-errors from a 13-week single-RR design that was superseded.

**Recommendation: 1,570 is authoritative. Double round-robin (24 rounds) is correct.**

The brief must be updated to remove:
- "each team plays all other 12 exactly once"
- "12-game round-robin + 1 bye week per team"
- Validation line "Each team plays exactly 12 regular-season games"
- Validation line "Each team has exactly 1 bye week in weeks 1–24"
- Validation line "Home/away counts for weeks 1–24: 6 home, 6 away per team"

And replace with the actual double-RR numbers (22–23 regular-season games per team, 3–4 bye weeks, 10–12 home/away).

---

### 2. DB Counts

**✅ PASS — all counts match expectations**

| Check | Expected | Actual |
|-------|----------|--------|
| Total games (season 1) | 1,570 | **1,570** |
| Regular games (weeks 1–24) | 1,440 | **1,440** |
| Rivalry games (weeks 25–26) | 130 | **130** |
| Rivalry pairs | 65 | **65** |
| Double-booking violations | 0 | **0** |

Per-team regular-season game counts: min=22, max=23 across all 130 teams. The asymmetry (110 teams at 22, 20 teams at 23) is expected for a 13-team double RR run through only 24 of 26 rounds — some matchups repeat the pairing from round 1. No team is over- or under-scheduled.

---

### 3. Intra-Tier Same-Conf Rivalry Pairs

**✅ PASS — 0 violations**

SQL query returned 0 rows. All 65 rivalry pairs are either cross-tier or cross-conglomerate (or both). The brief's preference rule was satisfied without any fallback.

---

### 4. Migration Chain

**✅ PASS — linear chain confirmed**

```
<base> -> 33f31770f03e (programs_schema)
       -> a1b2c3d4e5f6 (games_schedule_schema)   ← this feature
       -> 36a6ee9b555e (players_schema)
       -> b2c3d4e5f6a7 (head) (staff_schema)
```

The games migration (`a1b2c3d4e5f6`) correctly chains from `33f31770f03e` (programs). No branches, no gaps.

---

### 5. Game Model — Nullable program IDs

**⚠️ NOTE — nullable is intentional per the brief schema, but worth a decision before sim-engine**

The `Game` model and the migration both declare `home_program_id` and `away_program_id` as `nullable=True`. This matches the brief's schema verbatim:

```sql
home_program_id INTEGER REFERENCES programs(id),   -- no NOT NULL
away_program_id INTEGER REFERENCES programs(id),   -- no NOT NULL
```

The brief's schema uses nullable FK columns without `NOT NULL`, which in Postgres means nullable. This was likely intentional to allow future use cases (e.g. TBD opponents, neutral-site placeholders, or forfeit rows), since no game in the current seed has a null program ID.

**Recommendation:** For the sim engine, a game with a null `home_program_id` or `away_program_id` cannot be simulated. Two options:

- **Option A (preferred):** Keep nullable in the model (matches brief). Add a DB constraint or application-level guard in the sim engine that only picks up games where both IDs are non-null and `status = 'scheduled'`.
- **Option B:** Add `NOT NULL` constraints now via a new migration. This is cleaner but diverges from the brief schema and breaks any future use of null-program rows.

This is a design decision for the sim-engine implementer, not a bug in schedule-gen.

---

### 6. Sample Rivalry Pairs — Geographic Sense

**✅ PASS — geographically coherent pairs dominate**

Sampled 15 pairs:
- Within-state pairs are common and sensible: Oregon Polytechnic (Albany OR) vs Western Oregon Institute (Salem OR), Washington Institute (Tacoma WA) vs Washington Polytechnic (Yakima WA), Tupelo University (Tupelo MS) vs Mississippi Tech (Meridian MS), Maryland Institute (Frederick MD) vs Chesapeake Military Institute (Waldorf MD), North Carolina Tech (Greensboro NC) vs Hickory University (Hickory NC).
- Adjacent-state pairs are reasonable: Tennessee A&M (Kingsport TN) vs Clarksville University (Clarksville TN — same state, different conf), Iowa Institute (Cedar Rapids IA) vs Illinois Academy (Waukegan IL).
- The most geographically stretched pair in the sample is Northern Texas University (Bryan TX) vs Altoona University (Altoona PA) — cross-continent. This is expected as a fallback when no nearby cross-conf partner was available.

No problematic pairs found in the sample.

---

### 7. Coverage — All 130 Programs Present

**✅ PASS — confirmed**

- Programs in regular schedule (weeks 1–24): **130 / 130**
- Programs in rivalry pairs: **130 / 130**
- All programs appear in both halves of the schedule.

---

## Items Requiring a Decision Before Sim Engine

| # | Decision | Recommendation |
|---|----------|---------------|
| 1 | **Update the brief** to remove contradictory single-RR language. The 1,570 / double-RR interpretation is correct. | Accepted — brief needs a patch before the next role reads it. |
| 2 | **Nullable program IDs in `games`**: keep nullable + guard in sim engine (Option A) or add NOT NULL migration now (Option B). | Option A — defer to sim engine; keep schema flexible. |
| 3 | No `relationship()` wired on `Game` or `RivalryPair` models. | Acceptable for now; sim engine will add FK relationships when it needs to join. |

---

## Summary

The schedule-gen implementation is complete and correct. The DB matches all expected counts, no team is double-booked, rivalry pairs are clean, and the migration chain is linear. The only action required before proceeding is updating the brief to drop the contradictory single-RR language. The nullable program ID question is a minor design note for the sim-engine team.
