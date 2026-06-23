# Retro — gridiron: play_log Multi-Player Attribution

**Role:** retro
**Sequence:** add-feature
**Date:** 2026-06-23

---

## Project

`gridiron-play-log-attribution` — `add-feature` sequence. Single session. Roles that ran: brief → planner → architect → implementer → reviewer → retro. Python-only, no frontend. All 6 success criteria met. Verdict: PASS WITH NOTES.

---

## What Went Well

**W1 — Architect pre-reading the engine files before writing specs:** The architect role read `play_resolver.py`, `game.py`, and the existing migrations before writing the spec. This meant the "exact code snippets the implementer can drop in" section was accurate — no rework at implementation time. This should be the default for `add-feature` sequences touching existing code: architect always reads the relevant source files, not just the planner output.

**W2 — Single-point `_to_row()` abstraction:** The existing `_to_row()` pattern in `game.py` meant the 5 new columns required exactly one dict extension rather than changes scattered across two game loops. The architect identified this as a leverage point and the implementer exploited it. This is a sign of good existing architecture.

**W3 — Live game verification as integration test:** Running `_run_game_sync(game_id)` and querying the new columns by play type is a complete end-to-end check in ~10 seconds. This is faster and more trustworthy than unit tests for this class of change. Worth codifying as the standard verifier for engine changes.

**W4 — Ponytail discipline:** No over-engineered abstractions. The `dl_player_id = primary on SACK` intentional redundancy was correctly flagged with a comment rather than being silently added or silently rejected — the "ponytail: comment naming the simplification" pattern worked exactly as intended.

---

## What Could Have Gone Better

**B1 — Planner field-assignment table had phantom play types:** The planner output included `RUSH_TD` and `PASS_TD` as rows in the field-assignment table. These don't exist as play types in the engine — the engine produces `RUSH` → then `TOUCHDOWN` as a separate row when it crosses the goal line. The planner couldn't know this without reading the engine code. The architect had to silently resolve this. **Improvement:** In `add-feature` sequences touching an existing engine, the planner role should be instructed to read the source file for play types before writing the field-assignment table, or the architect should explicitly surface resolved phantom types in its output.

**B2 — Project-state.md was stale:** `_config/project-state.md` still described the initial gridiron build (`new-project-full` sequence, step 1 complete). It was not updated between the gridiron v1 completion and this `add-feature` sprint. The retro role had to infer the session arc from the brief output and conversation context rather than reading authoritative state. **Improvement:** Update `project-state.md` when a sequence completes, not only during retro.

**B3 — Brief handoff questions to planner were too broad:** The brief asked the planner to "confirm the full field-assignment table per play type" — but the planner also can't read engine source (role boundary). The brief should ask the architect to confirm the field-assignment table, not the planner. The planner's job is requirements and scope, not internal engine routing.

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| Planner | Loaded `python-conventions.md` in full; most of it (HuggingFace, SQLAlchemy asyncpg rules) is irrelevant to an engine-only add-feature | Medium | Add a "slim mode" note to `add-feature` sequence: planner only loads the top 20 lines of conventions (package manager, formatter, type hint rules) |
| Architect | Read `roles/architect/output/output.md` (previous year-zero content, 550 lines) before overwriting | Low | Not avoidable — required by Write tool. Acceptable. |
| Reviewer | Had to read full `play_resolver.py` to review 7 changed return sites — most of the 300-line file is unchanged context | Low | For `add-feature` reviews, implementer should provide a diff-only section in output.md showing exactly which lines changed |

### Redundancy Patterns

- The field-assignment table was written three times: once in the plan doc, once in the planner output, once in the architect output. In `add-feature`, one authoritative table in the architect output is sufficient — planner can describe the table at a high level and defer to architect for the exact cell values.

### Scoping Recommendations

- In `add-feature` sequences: planner does NOT need `vibecoding-style.md` (style guidance is for new-project pacing, not feature additions). Remove from planner inputs for this sequence.
- Architect reads engine source directly — add this as an explicit step in the `add-feature` architect process: "Read the files listed in planner's 'Files Changed' table before writing interface specs."

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `resources/routing.md` | In `add-feature` architect step: add "Read each file listed in the planner's Files Changed table before writing interface specs" | B1 — architect needs source context, not just planner output | No |
| `resources/routing.md` | Remove `vibecoding-style.md` from planner inputs in `add-feature` sequence | Token efficiency — pacing guidance doesn't apply to feature additions | No |
| `resources/routing.md` | Add note to `add-feature` brief step: "Do not ask planner to confirm internal engine routing — route field-assignment table questions to architect instead" | B3 — wrong role was asked to confirm implementation details | No |

### Skills to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `skills/engine-verification.md` (new) | Create: describe the `_run_game_sync(game_id)` + SQL sampling pattern as the standard verifier for gridiron engine changes | W3 — this pattern is reusable and worth codifying | No |

### Routing Changes

| Sequence | Change | Reason | Human decision required? |
|----------|--------|--------|--------------------------|
| `add-feature` | Add to implementer output template: "Diff Summary section listing file + line ranges changed" | Reduces reviewer context load when reading large gitignored files | No |

### New Resources or Skills Needed

- `skills/engine-verification.md`: a ~20-line file documenting the gridiron verification pattern: re-run a completed game via `_run_game_sync`, query `play_log` by `game_id`, group by `play_type`, check column nullability. Include the exact SQL template. Would have been useful for the implementer to load without re-deriving it.

---

## One Change to Make Now

**`resources/routing.md` — architect input in `add-feature` sequence.**

Add to the architect row's Notes column:
> "Read each source file listed in planner's Files Changed table before writing interface specs. For engine/gitignored files, this is the only way to know variable scope, existing patterns, and what already exists."

This prevents the phantom play type issue (B1) and ensures the architect's spec is grounded in actual code, not just the planner's description of the code.

---

## Handoff

Human reviews this output. Recommendations above are applied manually to workspace files. Update `_config/project-state.md` to:
- Mark `gridiron-play-log-attribution` `add-feature` sequence complete
- Record that retro ran 2026-06-23
- Update "Active Project" to reflect gridiron is now in maintenance mode (or whatever the next sprint is)
