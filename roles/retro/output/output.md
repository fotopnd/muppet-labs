# Retro — gridiron: Defensive Position Expansion + Pass Rush Pre-Picks

**Role:** retro
**Sequence:** add-feature
**Date:** 2026-06-23

---

## Project

`gridiron-defensive-positions` — `add-feature` sequence. Single session. Roles: brief → planner → architect → implementer → reviewer → retro. Python-only, no frontend. All success criteria met. Verdict: PASS WITH NOTES.

---

## What Went Well

**W1 — Architect source-reading rule eliminated phantom types:** The routing.md rule added in the previous retro ("architect must read source files before writing specs") was enforced. The architect read `play_resolver.py`, `game.py`, `seed_roster.py`, and the previous migration before writing specs. Result: no phantom play types, no incorrect variable scope assumptions, no rework at implementation time. The rule is paying off.

**W2 — Clean deterministic migration design:** `player_id % 2` split is deterministic, reversible, and produces roughly equal pools (LOLB=371, ROLB=409, SS=395, FS=385). No randomness, no state to preserve. This is the right pattern for position-code migrations.

**W3 — `_pick()` None-safety held across all new groups:** `s_coverage = _pick(defense.get("S", []))` returns None cleanly if the S group is empty (e.g. old games run before migration, or DB group lookup mismatch). No guard code needed. The existing `if sacker else None` pattern handles it uniformly across all 6 attribution fields.

**W4 — Single INSERT site minimised game.py surface:** Only one SQL string to update for `s_player_id` (OT drive feeds the same `plays` list). `_to_row()` is a clean abstraction — one dict key addition covered all paths.

---

## What Could Have Gone Better

**B1 — Verification ran on an already-complete game (game 13) first:** The implementer's first attempt ran `game 13` which was already complete. This produced duplicate play_log rows (282 total vs expected ~142) and gave misleading 50% attribution rates. The issue was caught and corrected by running game 19 (a scheduled game), which showed 100% attribution. **Fix:** Add to the engine verification pattern: always query `status='scheduled'` before running a game. If no scheduled games exist, document that explicitly.

**B2 — SACK `dl_player_id` semantic shift not documented in code:** The previous sprint had `dl_player_id = def_slot.player_id` on SACK rows (intentionally mirroring primary — query convenience). This sprint changed SACK to use pre-picked `dl_rusher` separately from `lb_rusher`, so `dl_player_id` is now NULL when DL pool is empty (rare but possible). Any query assuming `dl_player_id = primary_player_id` on SACK rows may need to union with `lb_player_id`. Worth a ponytail comment in the SACK branch and a note in `project-state.md`.

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| Architect | Read `game.py` in full (594 lines) to find `_to_row()` and the INSERT site | Low | Acceptable — necessary to verify there’s only one INSERT. On larger files, architect could load only the relevant function range. |
| Retro | Previous retro output (400+ lines) loaded as "existing" before being overwritten | Low | Not avoidable — atomic write requires reading first. Acceptable. |

### Redundancy Patterns

- Field-assignment table appeared in brief output, planner output, AND architect output. Planner’s version was the most detailed and served as the definitive spec — architect re-stated it cleanly. The brief version was too high-level to be useful downstream. In future: brief describes the table shape, planner owns the authoritative table, architect confirms it.

### Scoping Recommendations

- In `add-feature` verify step: explicitly filter for `status='scheduled'` games. Add this to the engine-verification skill if one is created.

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `_config/project-state.md` | Update `play_log attribution` section: note that `dl_player_id` on SACK rows is no longer guaranteed to mirror `primary_player_id` (changed in this sprint) | B2 — query writers need to know this | No |
| `_config/project-state.md` | Add sprint summary: defensive-positions complete, 7-code taxonomy, `s_player_id` added, LB/DB/S independently addressable | Track completion | No |

### Skills to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| (none yet) | If/when `skills/engine-verification.md` is created (recommended by prior retro), add note: "Always query `status='scheduled'` before running a verification game; completed games produce duplicate play_log rows" | B1 | No |

### Routing Changes

| Sequence | Change | Reason | Human decision required? |
|----------|--------|--------|--------------------------|
| `add-feature` | No changes needed — current sequence worked cleanly | — | — |

### New Resources or Skills Needed

- The `skills/engine-verification.md` skill recommended in the previous retro is still not created. It would have prevented the game 13 duplicate-row issue. Worth creating before the next engine sprint.

---

## One Change to Make Now

**Update `_config/project-state.md`** to record the completed sprint and the SACK `dl_player_id` semantic change.

Specific additions:
1. Under completed sprints: add `gridiron-defensive-positions` row
2. Under play_log attribution section: add note that `dl_player_id` on SACK rows is set from `dl_rusher` (pre-pick), not from the sacker directly. If DL pool empty, `dl_player_id=NULL` and `lb_player_id=primary_player_id` on that play.
3. Record the new POSITION_GROUPS: LB=[LOLB,MLB,ROLB], DB=[CB,DB], S=[SS,FS]

---

## Handoff

Human reviews this output. Update `_config/project-state.md` per the "One Change to Make Now" above. Create `skills/engine-verification.md` if the next sprint touches the engine again.
