# Reviewer Output — gridiron: Coaches Pages

**Role:** reviewer
**Sequence:** add-feature
**Date:** 2026-06-24

---

## Summary

Implementation is correct. The two-CTE SQL pattern correctly separates game-level W-L aggregation from play-level yardage stats, fixing the multiplication bug found during implementation. Backend API verified live (200 + 404). Frontend builds clean. One minor edge case noted (NULLable play_stats join) but COALESCE coverage makes it safe.

---

## Correctness

**C1 — Two-CTE SQL pattern is correct (confirmed):** `wl` CTE aggregates wins/losses at game level (`COUNT(*) AS games_played`, `SUM(won)`). `play_stats` CTE joins play_log against coach_games — no multiplication of game rows into W-L count. Live API call confirms: program 1 shows wins=0, losses=1, games_played=1 (not 138). ✓

**C2 — COALESCE on aggregated stats is correct:** `COALESCE(SUM(CASE ... END), 0)::int` protects against NULL when no matching plays exist for a game. The outer `wl LEFT JOIN play_stats` always finds a match since play_stats also groups by season from coach_games. ✓

**C3 — win_pct division guard:** `round(r["wins"] / r["games_played"], 3) if r["games_played"] else 0.0` — correct. `games_played` is `COUNT(*)` and `wl` only has rows for seasons with games, so this guard is technically dead code but harmless. ✓

**C4 — 404 handled correctly:** `.one_or_none()` → None check → HTTPException(404). Verified live: coach 9999999 returns 404. ✓

**C5 — Frontend TypeScript clean:** `pnpm build` exits 0, 91 modules, 0 errors. `CoachDetail.coach_id` correctly typed as `number` (not `int` — architect spec had a typo). ✓

**C6 — `def_yards_allowed` uses opponent possession correctly:** `pl.possession != cg.team_side` correctly identifies when the opponent has the ball. Since `team_side` is either 'home' or 'away', this is always the complement. ✓

**C7 — `off_yards` includes SACK (negative) yards:** A SACK occurs when the team has possession and loses yards. Including SACK yards in off_yards is correct (it reduces total offense, as in real football). `pass_yards` intentionally excludes SACK to show clean passing production — this discrepancy (off_yards ≠ pass_yards + rush_yards) is intentional and acceptable. Minor: could add a note in the page UI but not blocking.

---

## Style

Code matches existing router pattern (`programs.py`). Two separate DB fetches over one complex CTE join: cleaner to debug, minimal overhead at this scale. ✓

`CoachPage.tsx` structure mirrors `PlayerPage.tsx` cleanly: header card, content card with table, loading/error states. `Th`/`Td` components are re-implemented locally (not shared) — consistent with `PlayerPage.tsx` which also defines them locally. ✓

---

## Tests

No test suite — consistent with existing project policy. Live DB query verified directly. Build verification (ruff, pnpm build) passes.

---

## Refactor Candidates

**R1 — Shared `Th`/`Td` components:** Both `PlayerPage.tsx` and `CoachPage.tsx` define identical `Th` and `Td` locally. Could be extracted to a shared `StatTable.tsx` if more stat pages are added. Not worth it until a third page needs them.

**R2 — `off_yards` vs `pass_yards + rush_yards` discrepancy:** No comment or note explains why the columns don't sum to total. Acceptable for now; add a tooltip or footnote if users ask why pass+rush ≠ total.

---

## Verdict

**PASS WITH NOTES**

No blocking issues. SQL is correct, verified live. TypeScript build clean. Ready to proceed to retro.

---

## Handoff

No next role required — proceed to retro.
