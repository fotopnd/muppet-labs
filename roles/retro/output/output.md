# Retro — gridiron: Coach Sprint (units 01–04)

**Role:** retro
**Sequence:** feature-sprint
**Date:** 2026-06-25

---

## Project

`gridiron-coach-sprint` — `feature-sprint` sequence. 6 features decomposed into 4 units by sprint-planner. Units 01 and 02 ran sequentially; units 03 and 04 ran in parallel (one isolated worktree agent + one gitignored-only agent). Reviewer verdict: PASS WITH NOTES. One post-review fix applied (StaffTab sort). One mid-sprint design correction made by the human (DC blitz separation).

---

## What Went Well

**W1 — sprint-planner decomposition was accurate:** The ponytail pass correctly collapsed 6 features into 4 units (merged endpoint+UI, extracted schema migration as a blocker, parallelised 03+04). The dependency graph held — no unit needed to touch another's files. The manifest's `Files owned` table was the right coordination artifact.

**W2 — Parallel units had zero file conflicts:** Units 03 (gitignored engine) and 04 (API router + frontend) shared no files. The worktree isolation for unit 04 allowed a clean merge via fast-forward. The gitignored engine approach for unit 03 also worked correctly — no commits needed.

**W3 — Seed bug caught during verification, not production:** The `id % 5` same-bucket problem (all OCs getting 'power_run') was caught during the DB verification step right after the migration ran. The fix (`ROW_NUMBER() OVER (PARTITION BY role ORDER BY id)`) was applied before review. No user-visible bug shipped.

**W4 — Live runtime verification produced a real finding:** Reviewer curled the live endpoint, found StaffTab role sort broken (abbreviations vs full strings), and flagged it. The fix was one line. This is exactly what the reviewer's runtime verification step is for.

**W5 — User design correction integrated cleanly:** The "blitz_heavy is not a formation" note came in mid-sprint after the engine was written. The fix was clean: remove `blitz_heavy` from `_DC_CAPS`, rename `balanced` → `3-3-5`, add `dc_run_tendency` parameter, use it as a continuous sack modifier. No schema change needed. The decoupling of formation vs aggression is now cleaner than the original brief.

---

## What Could Have Gone Better

**B1 — Brief didn't specify actual DB role strings:** The StaffTab sort bug (`ROLE_ORDER = ['HC', 'OC', 'DC', 'ST']`) came from the brief using abbreviations that don't match what's actually in the DB (`'Head Coach'`, `'Offensive Coordinator'`, etc.). The brief should specify actual DB enum values, not assumed shorthand. This caused a reviewer catch that was avoidable at brief time.

**B2 — `blitz_heavy` as formation is a football conceptual error:** The sprint-planner and brief both defined `blitz_heavy` as a DC style alongside 4-3/3-4/nickel. A DC formation and a DC tendency are different things — any formation can be run with blitz pressure. This was caught by the human, not any role. The planner or architect should be checking domain realism for simulation attributes.

**B3 — StaffTab sort fix happened after reviewer, not before:** The sort bug was a simple string mismatch that any `curl /programs/1/coaches` call during implementation would have caught. The implementer should verify sort order at runtime, not just that the endpoint returns data.

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| Unit 03 agent | Gitignored engine files required multiple Read calls to find the right function locations — no file map was in the brief | Medium | Brief should include a "Key functions" section with file+line pointers for gitignored engine files |
| Unit 04 worktree agent | Agent read CoachPage.tsx cold with no pointer to the relevant component — had to scan the whole file | Low | Brief should cite the specific component and line range to edit |
| Sprint review | Reviewer loaded previous sprint's output.md rather than the fresh unit outputs | Low | Sprint retro runs once at the end of all units — reviewers should reference the manifest, not stale implementer outputs |

### Redundancy Patterns

- Units 01 and 04 both touched `ProgramDetail.tsx` and `schemas.py`. The brief correctly declared ownership, but the unit 04 agent re-read both files from scratch without knowing what unit 01 had already added. This is unavoidable with parallel-safe briefs, but the brief could include a "What unit 01 already added" section.

### Scoping Recommendations

- Engine briefs should include a short "File map" section: function name, file path, approximate line number. Gitignored files have no git blame or LSP — the agent must scan, which costs tokens.
- For units that extend a prior unit's output (unit 04 extending unit 01's `ProgramDetail.tsx`), the brief should summarise exactly what the prior unit added so the agent doesn't need to infer it from reading the file cold.

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `_config/project-state.md` | Already updated in this session | — | — |

### Skills to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `skills/sprint-agent-handoff.md` | Add: "For engine briefs (gitignored files), include a File map section: function, file, approximate line." | Reduces cold-scan token cost for gitignored file agents | No |

### Routing Changes

| Sequence | Change | Reason | Human decision required? |
|----------|--------|--------|--------------------------|
| `feature-sprint` brief step | Add guideline: "Briefs must use actual DB field values, not shorthand. If a brief refers to an enum/role string, quote the exact value from the DB or seeding SQL." | Prevents abbreviation/mismatch bugs like StaffTab sort | No |
| `feature-sprint` brief step | Add guideline: "For units that extend a prior unit's output, include a 'Prior unit added' section summarising exactly what was changed." | Prevents cold re-read of files the agent already has context on | No |

### New Resources or Skills Needed

- None — the issues found were brief-quality problems, not missing resources.

---

## One Change to Make Now

**Add to the `feature-sprint` brief template in `routing.md`:** briefs must quote actual DB field values (not shorthand), and engine briefs must include a File map (function + file + line). This prevents both the StaffTab sort bug and the gitignored-file scan overhead, which were the two most avoidable friction points in this sprint.

---

## Handoff

Recommendations above are notes only. The human applies changes to `routing.md` and `skills/sprint-agent-handoff.md` if desired. No blocking follow-up required — sprint is complete and verified.
