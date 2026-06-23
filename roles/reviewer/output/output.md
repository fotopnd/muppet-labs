# Reviewer Output — gridiron: play_log Multi-Player Attribution

**Role:** reviewer
**Sequence:** add-feature
**Date:** 2026-06-23

---

## Summary

Implementation is correct and complete. All 6 success criteria from the brief are verified by a live game run. One pre-existing description bug in the TFL play type is flagged (minor, pre-dates this sprint). One minor double-pick on fumble plays is noted but semantically correct. Both tracked files pass ruff. Ready to ship.

---

## Correctness

**C1 — OL players loading correctly (confirmed):** `POSITION_GROUPS["OL"]` activates 16 OL players per sample program. `build_roster_map` returns `"OL": 3 players` (top by snap weight). `ol_player_id` is non-null on all RUSH and PASS plays in the live game run. No issue.

**C2 — TURNOVER_FUMBLE double-pick on DL (minor, intentional):** On a fumble play, `dl_defender` is pre-picked from `defense.get("DL", [])`, and then `def_slot` is picked again from `defense.get("DL", []) or defense.get("LB", [])`. Both draws are from the same pool. The fumble recoverer (`def_slot`) is semantically independent from the pre-play DL attribution (`dl_defender`), so the double-pick is correct. But they could be the same player in both slots if the pool is small — `dl_player_id` and `tackler_player_id` could point to the same row. This is fine for the query use cases in the brief.

**C3 — Pre-existing TFL description bug (not introduced here, minor):** `play_resolver.py` TACKLE_FOR_LOSS returns `primary_player_id = rusher.player_id` and `description = _desc("TACKLE_FOR_LOSS", r_name, ...)` where `r_name = rusher.last_name`. The template is `"{player} stops the runner in the backfield"` — so the runner's name is placed where the tackler's name should go. This is a pre-existing bug, not introduced by this sprint. Logged for a follow-up fix but not blocking.

**C4 — RUSH picks placed after yards roll (correct, note only):** The `ol_blocker`, `dl_defender`, `lb_defender` picks occur after `yards = round(random.gauss(...))`. Ordering is fine — yards and picks are independent — but a reader might wonder why picks appear mid-function. The existing pattern of picks-before-branch is slightly violated here (picks are after the gauss call but before the branches). This is a clarity concern only, not a bug.

**C5 — All success criteria verified:**
- PASS_COMPLETE rows: `secondary_player_id` (QB) ✅, `ol_player_id` ✅, `dl_player_id` ✅
- RUSH rows: `tackler_player_id` ✅, `ol_player_id` ✅, `dl_player_id` ✅, `lb_player_id` ✅
- SACK rows: `secondary_player_id` (QB) ✅, `ol_player_id` (missed block) ✅

---

## Style

Both tracked files pass `ruff check` + `ruff format --check` after auto-fix. Engine files (gitignored) are not ruff-checked per project policy. No style issues on tracked files.

**S1 — Migration uses `sa.ForeignKey()` inline in `op.add_column` (matches convention):** Consistent with how `primary_player_id` was defined in `d4e5f6a7b8c9`. Correct.

---

## Tests

The engine files are gitignored and not in the test suite by policy. No existing tests cover `play_resolver.py` or `game.py`. The live game run (`_run_game_sync`) serves as the integration test — the verifier confirms all columns populated per spec.

**T1 — No unit test for `PlayOutcome` slot extension:** If a future change accidentally removes a slot name, there's no test to catch it. Could be a one-liner assert in a `__main__` block. Not blocking — engine is gitignored.

**T2 — No test for OL group in `POSITION_GROUPS`:** A trivial test would assert `"OL" in POSITION_GROUPS`. Worth adding to the existing test suite if one exists. Not blocking.

---

## Refactor Candidates

**R1 — RUSH picks ordering:** Move `ol_blocker`, `dl_defender`, `lb_defender` picks to immediately after `r_name =` (line 164), before the yards computation. This groups "all picks happen here" visually, matching the pass block pattern where `ol_blocker` and `dl_rusher` are picked before the probability roll. Minor clarity win.

**R2 — SACK `dl_player_id` comment:** The `ponytail: mirrors primary — query convenience` comment is correct and helpful. No change needed.

---

## Verdict

**PASS WITH NOTES**

No blocking issues. C3 (TFL description bug) is pre-existing and out of scope. C4 is a style note, not a bug. All attribution columns populate correctly per the success criteria.

---

## Handoff

No next role required. Human can proceed to retro.

Notes for retro:
- TFL description bug (`rusher.last_name` used as tackler name in template) is worth a 1-line fix in a follow-up pass
- R1 (picks ordering in RUSH block) is a cosmetic cleanup worth batching with a future engine edit
