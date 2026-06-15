# Retro — Glossary Tab

**Role:** retro  
**Sequence:** add-feature  
**Date:** 2026-06-14

---

## Project

`projects/red-team-platform/web/` — Glossary tab (6th tab) added to the dashboard. Frontend-only: three sections (Metrics, Attack Strategies with live ASR, Harm Categories). No backend changes.

**Sessions:** 1 (brief was pre-existing; implementer + reviewer + retro completed in a single resumed session after Wave 3b)  
**Roles run:** brief (archived, previous session) → implementer → reviewer → retro

---

## What Went Well

**W1 — Frontend-only scoping held.** The brief explicitly ruled out backend work and the implementer respected that boundary. `useStrategyComparison()` was already the right hook — no new endpoint needed. Live ASR data flows through with zero backend changes.

**W2 — Lib reuse: STRATEGY_DESCRIPTIONS and CATEGORY_LABELS.** Both already existed in `@/lib/`. The implementer identified and reused them rather than duplicating content inline. CATEGORY_DESCRIPTIONS (the only new data) was correctly kept inline in Glossary.tsx since it has a single consumer. The judgment call on where to put things was correct.

**W3 — MSW double-listen error not repeated.** A previous attempt on a different feature hit "cannot configure an already enabled network" by calling `server.listen()` inside the test file when `setup.ts` already handles it globally. This test correctly omitted the beforeAll/afterAll pattern.

**W4 — App.test.tsx stale names caught and fixed proactively.** Implementer caught that old tab name assertions (Coverage Heatmap, Strategy Comparison, Regression Tracker) would fail against the current 6-tab App.tsx and fixed them in the same pass. No reviewer catch needed.

**W5 — Graceful degradation by default.** `asr !== undefined ? <AsrBadge /> : <span>—</span>` and `STRATEGY_DESCRIPTIONS[key]` fallback to "No description available." are both correct-by-construction. Neither required a separate edge-case implementation pass.

---

## What Could Have Gone Better

**F1 — Misleading test name.** `Glossary.test.tsx:39` is named "renders all 13 harm category labels" but only asserts 3 of the 13. The name implies exhaustive coverage it doesn't provide. This slipped through implementer and was caught by the reviewer. Fix: rename to "renders sample harm category labels" or expand assertions to all 13.

**F2 — Brief taxonomy mismatch (legacy).** The brief lists Harm Categories using WildGuard semantic names (`cybercrime_and_intrusion`, `harmful_information_generation`, etc.) because it was written before the taxonomy classifier training confirmed actual output format (`LABEL_0–LABEL_12` with human labels from `categoryLabels.ts`). The implementation is correct, but the brief is now a misleading historical document. No action needed — this is inherent to the temporal gap between brief authoring and implementation. Noting for future brief authors: wait until classifier output format is confirmed before specifying category keys.

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| Reviewer | Loaded full `strategyDescriptions.ts` (305 lines) to confirm STRATEGY_DESCRIPTIONS reuse | Low | Acceptable — needed to verify the lib was the right source and all 13 WAVE_STRATEGIES had entries |
| Retro | `project-state.md` is 453 lines; retro only needed the last-session summary and next-action sections | Medium | Consider adding a "Session Header" (date, roles run, verdict) at the top of project-state.md so retro can read 20 lines instead of 453 |

### Redundancy Patterns

- The brief listed all 13 strategy descriptions in prose — these were also in `STRATEGY_DESCRIPTIONS`. Brief served as a discovery doc; redundancy acceptable since implementer didn't need to read the lib to know what existed.
- Reviewer output is longer than needed for retro consumption. Retro only needed verdict + gap list; the full checklist is for human review.

### Scoping Recommendations

- For frontend-only tasks under ~200 LOC, retro context can be reduced to: reviewer output (verdict + gaps only) + project-state.md last session summary. No need to load language conventions files unless a specific style finding requires it.

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `resources/routing.md` | Add `frontend-only-feature` as a named shortcut sequence: `brief → implementer → reviewer → retro` (skip architect and planner) with condition "when the brief explicitly rules out backend changes and scope is < 3 files" | This project confirmed the pattern works cleanly; codifying it avoids loading architect/planner unnecessarily for similar future tasks | No |

### Skills to Update

None.

### Routing Changes

| Sequence | Change | Reason | Human decision required? |
|----------|--------|--------|--------------------------|
| `add-feature` | Note in routing.md that if brief specifies "frontend-only, no backend changes", skip to `implementer` directly without architect/planner pass | Glossary tab was brief → implementer; worked cleanly with no architectural uncertainty | No |

### New Resources or Skills Needed

None. All tools and conventions already in place for this class of task.

---

## Code Fix to Apply (not a workspace change)

`web/src/test/Glossary.test.tsx:39` — rename "renders all 13 harm category labels" to "renders sample harm category labels", or expand to assert all 13 labels. Implementer pass or direct edit. Low priority; doesn't affect runtime or shipping.

---

## One Change to Make Now

**Add `frontend-only-feature` sequence to `resources/routing.md`.**

The Glossary tab confirmed that for frontend-only tasks where the brief explicitly rules out backend work and scope is ≤ 3 files, the sequence is: `brief → implementer → reviewer → retro` with no architect or planner step. Codifying this in routing.md will prevent unnecessary role invocations on future similar tasks.

---

## Handoff

Retro complete. Recommended actions:

1. Apply routing.md update (frontend-only-feature sequence note) — no human decision needed
2. Fix misleading test name in `web/src/test/Glossary.test.tsx:39` — low priority follow-up
3. Update `_config/project-state.md`: record Glossary tab shipped, reviewer verdict PASS WITH NOTES, retro complete; update Current State to next priority (Llama Guard baseline P2, portfolio deploy P3)
4. Git commit all new and modified files from this feature
