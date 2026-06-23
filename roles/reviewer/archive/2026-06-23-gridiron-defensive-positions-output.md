# Reviewer Output — gridiron: Defensive Position Expansion + Pass Rush Pre-Picks

**Role:** reviewer
**Sequence:** add-feature
**Date:** 2026-06-23

---

## Summary

Implementation is correct and complete. All success criteria from the planner verified by a live game run (game 19): PASS_COMPLETE/DEFLECTION/INCOMPLETE 100% lb+s, RUSH/SACK 100% lb, specials/TD 0% both. Position migration is clean — no OLB or S rows remain. One semantic change in SACK `dl_player_id` is noted (no longer guaranteed mirrors `primary_player_id`). Ready to proceed.

---

## Correctness

**C1 — Position split correct (confirmed):** `SELECT position, COUNT(*) FROM players GROUP BY position` shows LOLB=371, ROLB=409, SS=395, FS=385, CB=1040, MLB=520. No OLB or S rows. Parity split is deterministic by `player_id % 2`. ✓

**C2 — SACK `dl_player_id` no longer mirrors `primary_player_id` (warning, not blocking):** In the previous sprint, `dl_player_id = def_slot.player_id` on SACK rows was intentionally the same as `primary_player_id` (the sacker). Now `primary = sacker = dl_rusher or lb_rusher` and `dl_player_id = dl_rusher.player_id` independently. If DL pool is non-empty (always true in practice), `dl_player_id` still = `primary_player_id` when sacker comes from DL. If sacker falls back to `lb_rusher` (DL pool empty), `dl_player_id` is NULL and `lb_player_id` = primary. This is semantically correct and more accurate than the previous blanket assignment, but any query relying on `dl_player_id = primary_player_id` on SACK rows may need to change.

**C3 — Attribution 100% on all pass plays (confirmed):** Game 19 sample:
- PASS_COMPLETE 38/38 lb, 38/38 s ✓
- PASS_INCOMPLETE 17/17 lb, 17/17 s ✓
- PASS_DEFLECTION 4/4 lb, 4/4 s ✓
- TURNOVER_INTERCEPTION 1/1 lb, 1/1 s ✓
- SACK 3/3 lb (= lb_rusher always), 0 s (correct per planner table) ✓
- RUSH 35/35 lb, 0 s ✓

**C4 — `POSITION_DISTRIBUTION` assert at import time (confirmed):** Sum = 75 starters + 10 reserves = 85. Assert passes. Any future change that breaks the total will immediately fail on import. ✓

**C5 — PASS_DEFLECTION primary pick unchanged (correct):** `def_slot = _pick(defense.get("DB", []) or defense.get("DL", []))`. Deflections come from DB (corners/nickel batting the ball) or DL (tipped at line). Not changed to include S — safeties don’t typically bat passes at the line. Correct.

**C6 — `db_closer` on PASS_COMPLETE changed from `DB or LB` to `DB or S` (minor, acceptable):** The tackler on a completed pass (the "closer") now falls back to safeties rather than linebackers. This is more realistic for downfield completions (FS/SS are the deep closers). Previous `LB` fallback was a v1 approximation. Change is correct.

**C7 — TURNOVER_INTERCEPTION interceptor pick expanded to `DB or S` (minor, correct):** Previously picked from `DB` only (corners/nickel). Safeties intercept passes too. The expansion is realistic.

**C8 — Downgrade order correct:** `downgrade()` drops `s_player_id` column first, then reverts S→SS/FS, then OLB→LOLB/ROLB. Correct order — column drop before position revert (the column FK references players.id, not position codes). ✓

---

## Style

Tracked files pass ruff check (2 auto-fixed in migration). Pre-existing E501/E731 violations in `seed_roster.py` (docstring, SQL, lambda in `draw_attrs`) are not introduced by this sprint. Engine files (gitignored) not ruff-checked per project policy.

**S1 — Migration format consistent with `a7b8c9d0e1f2`:** Same `from __future__ import annotations`, `Sequence` from `collections.abc`, inline `sa.ForeignKey()`. ✓

---

## Tests

No test suite for engine files (gitignored by policy). Live game run serves as integration test. Position migration is a one-way data change — verified directly against DB.

**T1 — No test for `_pos_to_group("LOLB")` etc.:** If someone removes LOLB from `POSITION_GROUPS["LB"]`, affected players would silently get dropped from roster maps. A one-liner assert in a test file would catch this. Not blocking given gitignored engine policy.

---

## Refactor Candidates

**R1 — PASS block pre-pick ordering:** `lb_rusher` and `s_coverage` are inserted immediately after `dl_rusher`. All four pre-picks are now grouped together before the probability roll. This is the intended pattern and reads clearly. No change needed.

**R2 — Pre-existing ruff violations in `seed_roster.py`:** 10 E501/E731 errors were pre-existing. A cleanup pass (wrap long SQL strings, convert `base = lambda` to `def base()`) would clear these. Batch with a future non-engine change.

---

## Verdict

**PASS WITH NOTES**

No blocking issues. C2 (SACK `dl_player_id` semantic shift) is a correctly handled edge case, not a bug. All attribution columns populate correctly at 100% on applicable play types. Position migration is clean. Ready for retro.

---

## Handoff

No next role required — proceed to retro.

Notes for retro:
- C2: document the new SACK attribution semantics somewhere (e.g. a comment in `play_resolver.py` SACK branch, or a note in `_config/project-state.md`) so future query writers don’t assume `dl_player_id = primary_player_id` on all SACKs
- R2: queue ruff cleanup for seed_roster.py in a future non-sprint pass
- `DB` (nickel/slot) position code has 0 current players — will appear naturally when rosters are next re-seeded with the new distribution
