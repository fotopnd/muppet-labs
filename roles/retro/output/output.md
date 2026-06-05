# Retro — moderation-dashboard safety-signal additions

**Role:** retro
**Sequence:** `add-feature`
**Date:** 2026-06-06

---

## Project

`moderation-dashboard-safety-signals` — live flag rate on model cards + model disagreement analysis panel. Sequence: `add-feature`. Two sessions (brief written 2026-06-05; planner + implementer + reviewer 2026-06-05/06). Roles that ran: brief → planner → implementer → reviewer → retro. Architect, design-brief, frontend-architect, ui-reviewer all skipped (correct — planner confirmed the feature fit cleanly into existing structure).

---

## What Went Well

**Three open questions resolved with zero rework.**
The brief pre-identified the three structural unknowns (SQL approach, panel placement, pagination). The planner answered all three with explicit reasoning in a single pass. None resurface in the reviewer output. This is the brief/planner pattern working correctly — the human should keep using it for features where the implementation has real design choices.

**Separate `_LIVE_COUNTS_SQL` kept existing SQL untouched.**
The decision to not touch `_METRICS_SQL` was correct. Extending `_build_model_metrics` with an optional `live_counts` parameter preserved all three callers unchanged and made the new SQL easy to test in isolation. This pattern — adding a parallel helper rather than augmenting an existing query — is worth preserving.

**Pre-existing test failures disambiguated before review via `git stash`.**
Six test failures existed in the suite before this feature was built. Using `git stash` to confirm pre-existence prevented them from contaminating the reviewer's correctness assessment. The reviewer correctly assessed only the new tests. This is a good discipline to continue.

**`DisagreementPanel` built as a self-contained component.**
Wiring into `ModelComparison` was one import line and one JSX element. No state lifted, no prop threading. Clean separation made the reviewer's structural assessment trivial.

---

## What Could Have Gone Better

**Implementer output.md was never written.**
The implementer role ran entirely as inline code changes. No `roles/implementer/output/output.md` was produced. The reviewer role contract specifies this file as its primary input — the reviewer had to reconstruct what was built from conversation context and code inspection. This breaks the formal handoff chain and means any future session referencing this feature will need to re-read the code rather than the implementer's summary.

Root cause: in short add-feature passes where the plan is in the planner output, the implementer output.md feels redundant. But its purpose is archival and handoff, not planning. Even a 10-line output.md (files changed, key decisions, known gaps) would be sufficient.

**T1 gap: planner specified a seeded-Escalation test that the implementer downgraded.**
Planner requirement 11 said "at least one test asserts correctly shaped data from seeded disagreement rows." The implementer wrote an empty-DB shape test instead. The reviewer caught it. Root cause: the planner didn't assess fixture complexity — seeding linked `Escalation + Classification` rows in a test conftest requires understanding the ORM models and session lifecycle, which is non-trivial. The planner specified the test without knowing this cost.

**C2 (ModelPerformance mock gap) was foreseeable.**
Adding `live_event_count` and `live_flagged_count` as required fields to `ModelMetrics` should have triggered a grep for all test mocks using that type. It didn't, and the reviewer caught it. There is no workspace convention that says: "when adding required fields to a shared type, update all test mocks." vitest's esbuild transpiler silently swallows TypeScript compile errors from missing required fields — they don't crash, they just produce `undefined`. This makes the gap invisible until a reviewer reads the test file.

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| All roles | `project-state.md` is 280+ lines; retro/reviewer only needed ~30 lines of current state | Medium | Split into `project-state-current.md` (≤50 lines, active context) and `project-state-archive.md` (decisions log, session history) |
| Retro | `routing.md` is 240 lines; retro only needed the `add-feature` section and retro role notes | Low | Acceptable — routing is fast to scan |
| Reviewer | No `implementer/output.md` to read; reviewer inspected code directly from memory | Low | Writing output.md would have saved re-derivation cost in this session; higher payoff for long-lived projects |

### Redundancy Patterns

The planner output reproduced the brief's SQL assumption confirmation verbatim ("confirmed from brief"). This is correct per the planner contract but the brief is already in context. The planner's Confirmed Assumptions section is useful to downstream roles as a summary — keep it, but note it should be terse (one line per assumption, not a full re-statement).

### Scoping Recommendations

- For `add-feature` passes: limit planner context to brief output + project-state.md header only. The full 280-line project-state is not needed — the planner needs current objective and file map, not session history.
- The reviewer role should explicitly list which files it read and which were already in context from implementer output.md. Currently the reviewer contract says "read each code file listed in the implementer's file manifest" but when there is no manifest, the reviewer falls back to reading everything, which is wasteful.

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `resources/typescript-conventions.md` | Add note under Testing section: "When adding required fields to a shared TypeScript type, grep all test mock objects using that type and update them. vitest's esbuild transpiler silently swallows missing required field errors — the test won't crash, but the new field will be `undefined` at runtime." | Prevents C2 class of reviewer finding recurring | No |
| `resources/python-conventions.md` | Add note under Testing section: "When a test requirement involves multi-table fixture creation (e.g. linked Escalation + Classification rows), note the fixture complexity in the planner output — do not specify the test without assessing whether the conftest can support it." | Prevents T1-class planner/implementer mismatch | No — add to planner CONTEXT.md instead (see below) |

### Skills to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| — | — | — | — |

### Routing Changes

| Sequence | Change | Reason | Human decision required? |
|----------|--------|--------|--------------------------|
| `add-feature` | Add note: "Implementer must write `roles/implementer/output/output.md` even for small passes. Minimum: files changed, key decisions, known gaps. Reviewer uses this as primary input." | Prevents formal handoff gap; output.md is archival, not planning | No |

### New Resources or Skills Needed

None.

### Role Contract Updates Needed

**`roles/planner/CONTEXT.md` — Requirements section**
Add to the Notes at bottom:
> When a requirement involves test fixture creation (seeding records across multiple related tables), note the fixture complexity inline: "requires new conftest fixture with [table A] + [table B] linked by [FK]." This lets the implementer scope the test correctly rather than silently downgrading to a weaker assertion.

**`_config/project-state.md` — structure**
Consider restructuring to two logical sections with a clear divider:
- **Current State** (≤50 lines): active project, objective, next action, known environment — rewritten each session
- **Session Archive** (append-only): decisions log, session summaries — never rewritten

Retro and reviewer would load only the Current State header. The full file is only needed for project planning and brief roles.

---

## One Change to Make Now

**Add the required-field grep convention to `resources/typescript-conventions.md`.**

In the Testing section, after the existing vitest/msw paragraph, add:

```
- When adding required fields to a shared TypeScript type (e.g. `ModelMetrics`), run
  `grep -r 'TypeName' src/test/` and update all mock objects. vitest's esbuild transpiler
  silently ignores missing required fields — the new field will be `undefined` at runtime
  rather than raising a compile error. The reviewer will catch it, but it is faster to fix
  at implementation time.
```

This is a 4-line addition, immediately actionable, and prevents a recurring reviewer catch that has now appeared once.

---

## Handoff

Human reviews recommendations above. Suggested actions before the next project:

1. **(Now)** Add the required-field grep note to `resources/typescript-conventions.md` Testing section (text above is ready to paste).
2. **(Before next add-feature)** Add the implementer output.md note to `routing.md` add-feature sequence.
3. **(Before next add-feature)** Add the fixture-complexity note to `roles/planner/CONTEXT.md`.
4. **(Optional, longer term)** Restructure `_config/project-state.md` into Current State header + append-only archive.

Update `_config/project-state.md` to record retro complete.
