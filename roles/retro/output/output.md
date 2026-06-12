# Retro — portfolio-site

**Role:** retro  
**Sequence:** new-project-full  
**Date:** 2026-06-12

---

## Project

**Name:** portfolio-site  
**Sequence:** `new-project-full` (all 9 steps)  
**Sessions:** 1 (single continuous session 2026-06-12)  
**Roles run in order:** brief → planner → architect → design-brief → frontend-architect → implementer → ui-reviewer → reviewer → retro  
**Reviewer verdict:** PASS WITH NOTES (3 minor items, all fixed before retro)

---

## What Went Well

**W1 — Metric values extracted from SUMMARY.md files at architect stage.**  
The planner flagged that exact metric values needed to be sourced from the project SUMMARY.md files rather than invented. The architect did this at step 3, producing a complete `projects.ts` data spec with real numbers. The implementer copied it verbatim — no correction pass needed. Pattern: when a planner open question involves factual data that exists in the workspace, resolve it at the architect stage (not the implementer stage) so the implementer has a complete spec to follow.

**W2 — BioSection generalisation caught and corrected before architecture was written.**  
The initial architect spec used hiring-goal language ("targeting Anthropic Safeguards"). The human corrected this to CV-grounded content before the architect output was finalised. The correction was a single targeted edit. Pattern: the architect role is the right place to catch copy-level decisions (not the implementer), because the copy propagates forward unchanged.

**W3 — Tailwind v4 shorthand token utilities worked cleanly.**  
The frontend-architect spec used `bg-[--color-*]` arbitrary syntax. At implementation time, this was correctly replaced with shorthand tokens (`bg-canvas`, `text-text-primary`, etc.) matching the error-hide-seek pattern already in the workspace. The implementation required no rework. Pattern: checking an existing Tailwind v4 project (`error-hide-seek`) before writing the implementer code avoided a silent CSS generation failure.

**W4 — Playwright verification caught no issues on first pass.**  
The ui-reviewer used headless Playwright to verify all 10 done criteria programmatically. All passed first time. The done criteria were specific enough (bounding-box y-coordinates, scrollWidth checks, computed background colours) that the verification was mechanical rather than interpretive.

**W5 — Three reviewer findings were all minor and fixed in under 5 minutes.**  
`mt-auto` removal (1 line), `githubUrl` field removal (4 lines across 2 files + test), `aria-label` addition (1 line). The codebase was clean enough that the reviewer had nothing blocking to report.

---

## What Could Have Gone Better

**B1 — `frontend-architect` spec used `bg-[--color-*]` arbitrary syntax that doesn't support opacity modifiers.**  
The frontend-architect output specified `hover:border-[--color-accent]/60` — which is valid Tailwind v4 syntax only if the color is in `@theme` AND the opacity modifier syntax is supported for CSS variable references. In practice the implementer replaced this with `hover:border-accent/60` (shorthand) which does support opacity modifiers. The frontend-architect spec should use shorthand token utility classes directly, not the arbitrary `[--color-*]` form, because (a) it matches the actual output and (b) shorthand is unambiguous about opacity modifier support.  
→ **Fix:** Update `design_style.md` or `typescript-conventions.md` to note that Tailwind v4 `@theme` color tokens should be referenced via shorthand utilities (`bg-canvas`, `text-accent`) not the `bg-[--color-*]` arbitrary form.

**B2 — `githubUrl` field typed and seeded but never rendered.**  
The architect spec included `githubUrl: string | null` in the `Project` type because it seemed likely to be needed. It was never wired into the UI. The reviewer caught it, the implementer removed it. This is a classic YAGNI violation in the data modelling phase. The architect should only type fields that the implementer will render.  
→ **Fix:** Add a note to `roles/architect/CONTEXT.md`: "Define only fields that the current implementer pass will render. Do not forward-model fields for hypothetical future UI."

**B3 — `mt-auto` redundancy in ProjectCard was a logical error in the frontend-architect spec.**  
The frontend-architect spec specified both `grow` on the description `<p>` and `mt-auto` on the demo `<div>`. These are mutually exclusive — `mt-auto` is a no-op when a sibling above it has `grow`. The reviewer caught it, the implementer fixed it. This is a spacing logic error that should be caught at the frontend-architect stage.  
→ **Fix:** No resource change needed. Awareness note: in a `flex flex-col` container, `grow` on one child and `mt-auto` on the following child are not additive — `mt-auto` becomes inert. The frontend-architect should apply one or the other.

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| Architect | Loaded full `design_style.md` (116 lines) but only the Marketing/Landing Page context section (10 lines) was relevant | Low | Already scoped correctly — design-brief confirmed context before architect ran. No change needed. |
| Frontend-architect | Loaded `setup-design-tokens.md` skill (116 lines) which prescribes a `tailwind.config.js` approach; Tailwind v4 does not use this file | Medium | The skill is v3-era. Frontend-architect noted this and used the `@theme` approach from the architect output instead. Skill should be updated to cover v4. |
| Implementer | Read `setup-ts-pnpm.md` (193 lines) — most of the setup was already done by the Vite 8 scaffold | Low | Scaffold included more deps than expected (typescript-eslint, react-hooks plugin). The skill's "Step 3 — Add ESLint and Prettier" section was partially superseded. No change needed for now; note in skill that Vite 8 scaffold bundles more. |

### Redundancy Patterns

- The `@theme` token block was specified in full in both the architect output and the frontend-architect output. The frontend-architect could have referenced "use the token block from `roles/architect/output/output.md` §Token Layer" rather than repeating it.
- The `PROJECTS` data spec appeared in full in the architect output and was copied verbatim to `projects.ts`. This is correct (the implementer needs the exact spec) — not redundancy, just handoff.

### Scoping Recommendations

- **Frontend-architect:** does not need to reload `vibecoding-style.md` — it was already loaded in design-brief and does not affect layout decisions. Remove from the routing.md resource list for frontend-architect.
- **Retro:** confirm that not loading language conventions files is the right call. It was — this retro needed no TypeScript reference.

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `resources/typescript-conventions.md` | Add a Tailwind v4 subsection under UI conventions: "Use shorthand token utilities (`bg-canvas`, `text-accent`) not arbitrary `bg-[--color-*]` syntax. Shorthand supports opacity modifiers; arbitrary syntax does not." | B1 — prevents the frontend-architect/implementer mismatch on token syntax | No |

### Skills to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `skills/setup-design-tokens.md` | Add a Tailwind v4 section at the top: "For Tailwind v4 projects, skip Steps 2–6. Define tokens in `src/index.css` using an `@theme {}` block with `--color-*` and `--font-*` variables. No `tailwind.config.js` is needed. Use shorthand utility classes (`bg-canvas`, `text-accent`) to reference tokens in components." | B1, token efficiency B — the skill currently only covers v3 patterns | No |
| `skills/setup-ts-pnpm.md` | Add a note under Step 3: "Vite 8 scaffold (`pnpm create vite --template react-ts`) bundles `@eslint/js`, `typescript-eslint`, `eslint-plugin-react-hooks`, `@types/node`, and `globals` by default. Skip installing these manually; only add `prettier` and the testing libs." | Token efficiency — prevents redundant install steps being listed | No |

### Routing Changes

| Sequence | Change | Reason | Human decision required? |
|----------|--------|--------|--------------------------|
| `new-project-full` step 5 | Remove `vibecoding-style.md` from frontend-architect resources | Not referenced in frontend-architect output; design-brief already loaded it | No |

### New Resources or Skills Needed

Nothing critical. The workspace handled a fully static frontend project cleanly with existing infrastructure.

---

## One Change to Make Now

**Update `skills/setup-design-tokens.md`** — prepend the Tailwind v4 note at the top so the next frontend-architect that loads this skill gets the correct pattern immediately rather than reading a v3-oriented procedure and having to adapt it.

Exact addition at line 1 (before "# Skill: Setup a TypeScript / React Project"):

```markdown
## Tailwind v4 Projects

For Tailwind v4 (identified by `@tailwindcss/vite` in devDependencies):
- **Skip Steps 2–6 below.** No `tailwind.config.js` is created.
- Define tokens in `src/index.css`:
  ```css
  @import "tailwindcss";
  @theme {
    --color-canvas: oklch(...);
    --color-accent: oklch(...);
    /* etc. */
  }
  ```
- Reference tokens in components using shorthand utilities: `bg-canvas`, `text-accent`, `border-border`.
  - **Not** `bg-[--color-canvas]` — the arbitrary form does not support opacity modifiers.
  - Opacity modifiers work with shorthand: `bg-surface/95`, `hover:border-accent/60`.
- Accent hue is confirmed at the architect stage, not here.

The v3 procedure below applies to projects using `tailwind.config.js`.
```

---

## Handoff

Human reviews these recommendations and decides which to apply. The three skill/resource changes are low-risk and no human decision is required. The routing.md change (remove `vibecoding-style.md` from frontend-architect) is also straightforward.

Update `_config/project-state.md` to record retro complete and which recommendations were actioned.
