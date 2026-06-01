# Retro — case-queue

**Role:** retro | **Date:** 2026-06-01  
**Inputs:** `roles/reviewer/output/output.md`, `roles/implementer/output/output.md`, `_config/project-state.md`, `resources/routing.md`, `resources/vibecoding-style.md`

---

## Project

**Name:** case-queue  
**Sequence:** `new-project-full`  
**Sessions:** 1 (single sitting, 2026-06-01)  
**Roles that ran:** brief → planner → architect → implementer → reviewer → retro  
**Debug-fix runs:** 0  
**Blockers encountered:**
- `pnpm` not installed — resolved inline (`npm install -g pnpm`)
- `shadcn/ui` installation is interactive — resolved by switching to raw Tailwind CSS
- TypeScript 6 rejects `baseUrl` in tsconfig — resolved by removing it (paths alone sufficient)
- `import { defineConfig } from 'vite'` lacks `test:` type — resolved by using `vitest/config`
- `pydantic-settings` ValidationError on shared `.env` — resolved with `extra="ignore"`

---

## What Went Well

**1. Prior retro recommendations were applied**

The eval-harness retro identified four gaps: missing `skills/setup-uv-project.md`, missing `resources/python-conventions.md`, retro absent from routing sequence, and no archive convention. All four were addressed before this project started. Both setup skills (`setup-uv-project.md` and the new `setup-ts-pnpm.md`) were present at intake. The archive convention was followed correctly — both reviewer and retro outputs were archived before overwriting. The workspace is visibly improving across projects.

**2. Implementer self-documented deviations clearly**

The implementer output listed five deviations from the architecture with the reason for each. This made the reviewer's job mechanical: each deviation was already explained, so the reviewer confirmed or challenged rather than discovering. The double-commit concern was self-flagged by the implementer and cleared by the reviewer (correctly: `flush()` is within-transaction, commit is single). This is the intended loop.

**3. Role sequence ran without human intervention between roles**

No role needed to surface a blocking question. The architect's open questions all carried proposed answers. Handoff sections directed each subsequent role clearly. The only pauses were intentional sign-off gates.

**4. Reviewer findings were precise and ordered**

Two of the reviewer findings are labelled "blocking for ruff clean" (enums and unused import) with the exact fix stated. Non-blocking items are clearly separated. The severity gradient makes it unambiguous what must be done versus what is optional.

**5. Test architecture was clean**

Backend integration tests hit a real Postgres instance (per the architect decision to avoid mocks). Frontend tests mock at the hook layer (a convention deviation, but consistent and fast). The conftest.py pattern — session-scoped `create_all`, per-test truncate — is a solid repeatable pattern for SQLAlchemy async test setups.

---

## What Could Have Gone Better

**1. TypeScript conventions file was missing — same pattern as Python conventions in eval-harness**

`resources/typescript-conventions.md` did not exist at the start of this project. The decision log records it was created mid-session, before the architect ran. This is the second consecutive project where a language conventions file had to be created mid-sequence. The pattern suggests the workspace should confirm all required language resources exist before running `brief`, not discover the gap at the planner or architect stage.

**2. `skills/setup-ts-pnpm.md` was also missing — same pattern**

`skills/setup-ts-pnpm.md` did not exist. Created mid-session. Two setup skills were missing (Python in eval-harness, TypeScript here). Rust will be next. A pre-project checklist that confirms all needed skills exist would prevent this recurring gap.

**3. TypeScript 6 breaking changes not documented — caused a detour**

The architect spec included `baseUrl` in tsconfig. TypeScript 6 rejects `baseUrl` with a hard error when `moduleResolution: bundler` is active. This was discovered at implementation time, not at planning time. `typescript-conventions.md` was created during this session but did not include this gotcha (it was created before the detour occurred). The file needs updating.

Additionally, `vitest/config` vs `vite` for the defineConfig import is a non-obvious requirement. Both gotchas should live in `typescript-conventions.md` so the architect or implementer can avoid them next time.

**4. shadcn/ui specified by architect — implementation reality not documented**

The architect spec called for shadcn/ui. `npx shadcn@latest init` is interactive — it cannot run in a non-interactive session. The fallback to raw Tailwind was correct and fast, but the architect shouldn't recommend a tool whose installation flow is incompatible with the workspace's execution model without noting the workaround. `skills/setup-ts-pnpm.md` should document the shadcn/ui interactivity constraint and the Tailwind fallback.

**5. pydantic-settings `extra="ignore"` discovered at runtime**

The `.env` file is shared between the FastAPI backend and the Vite frontend. `pydantic-settings` raises `ValidationError` on unknown variables unless `extra="ignore"` is set. This is a predictable interaction when a shared `.env` pattern is used. It was not in the planner or architect output and had to be resolved during implementation. `python-conventions.md` should document this as a standard pydantic-settings pattern when shared env files are used.

**6. Retro archive convention not applied to retro itself**

The archive convention in `routing.md` describes archiving `roles/[role]/output/output.md` before overwriting. It applies to all roles. The previous retro output was archived correctly this session — but this required the executing role to check for a prior output and archive it manually. The retro's own `CONTEXT.md` process steps do not mention this. The convention should appear in every role's CONTEXT.md or be pulled from routing.md explicitly at step 0.

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| Reviewer | Reads full implementer output including 80-line "How to Run" section and setup steps — irrelevant to code review | Low | Add a `## Review Summary` section at the top of implementer output with: deviations, known gaps, flagged concerns. Reviewer reads this first; only loads full manifest if needed for context. |
| Reviewer | Role contract asks reviewer to "read each code file listed in the implementer's file manifest" — 30+ files for a fullstack project | Medium | Add a qualifier: "focus reads on files flagged by the implementer, plus all router/handler files. Read shared utilities only if a finding requires it." |
| Implementer | Loads `vibecoding-style.md` + `python-conventions.md` + `typescript-conventions.md` — for a polyglot project this is three resources plus the architect output | Low-Medium | For polyglot projects, define a combined conventions load in routing.md rather than loading each file separately. Or create a `fullstack-web.md` stub that delegates to the individual files. |
| All roles | Archive check (does a prior output exist, should it be archived) is implicit and requires a read at the start of every role | Low | Add step 0 to every role's CONTEXT.md Process section: "Archive any existing `output/output.md` to `output/archive/[date]-[project]-output.md` before writing." Eliminates the implicit check. |

### Redundancy Patterns

- The **project description** appears in brief output, planner output, architect output, implementer output header, and project-state.md. For a single-session project this is acceptable overhead. For multi-session projects it adds load on each context resumption.
- The **"How to Run" section** in implementer output is the right place for it — but it is read by the reviewer even though the reviewer never runs the code. The reviewer contract should scope its implementer read to specific sections.
- The **deviations table** in implementer output is exactly what the reviewer needs. It worked well as the primary input for the correctness assessment. This pattern should be made explicit in the implementer role contract: "the deviations table is the reviewer's primary input; populate it carefully."

### Scoping Recommendations

1. Add a `## Review Summary` section (5–10 lines) to the implementer output template. Contents: deviations, known gaps, specific concerns for reviewer. Reviewer reads this section before deciding which files to load.
2. In the reviewer's process steps, change "Read each code file listed in the implementer's file manifest" to "Read files flagged in the implementer's Review Summary, plus all router/handler files. Read others as needed for specific findings."
3. Add step 0 (archive check) explicitly to every role's CONTEXT.md process section — stops the implicit check from being missed.

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `resources/typescript-conventions.md` | Add subsection "## Known TypeScript 6 Breaking Changes": (1) `baseUrl` with `moduleResolution: bundler` raises an error — use `paths` only; (2) `import { defineConfig } from 'vite'` lacks `test:` typing — use `vitest/config` which re-exports all vite types | Two detours this project; prevent next time | No |
| `resources/python-conventions.md` | Add to the pydantic-settings section: "When a shared `.env` file is used (e.g. env shared with a frontend), add `extra="ignore"` to BaseSettings to prevent ValidationError on unknown variables." | Discovered at implementation time; predictable interaction | No |

### Skills to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `skills/setup-ts-pnpm.md` | Add a note under the component library step: "shadcn/ui (`npx shadcn@latest init`) is interactive — it cannot be run in a non-interactive session. Fallback: raw Tailwind CSS utility classes. The Tailwind implementation is portfolio-equivalent. If shadcn is required, document manual setup steps for the human to run." | shadcn fallback occurred this project; architect should be informed of the constraint before specifying it | No |

### Routing Changes

| Sequence | Change | Reason | Human decision required? |
|----------|--------|--------|--------------------------|
| All sequences | Add to the preamble (below the archive convention): "**Pre-role check:** Before the first role runs, confirm all language resources (`[lang]-conventions.md`) and setup skills exist for the target languages. If missing, create them before proceeding." | Same missing-resource gap occurred twice in two projects | No |

### New Resources or Skills Needed

**`resources/typescript-conventions.md` — update in place (see Resources to Update above)**

**Pre-project checklist (optional)** — a short `resources/pre-project-checklist.md` that lists what to verify before `brief` runs:
- Required language resource files exist
- Required setup skill files exist  
- `_config/project-state.md` is updated with active project name
- Known environment section is current

This is low priority for now (the workspace is small and the pattern is clear). Worth creating if a third "missing resource" gap appears in a future project.

### Role Contract Updates

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| All role `CONTEXT.md` files | Add step 0 to Process section: "Archive any existing `output/output.md` to `archive/[date]-[project]-output.md` before writing." | Archive convention is in routing.md but not in role contracts; roles should not depend on the executor knowing to check routing.md for this | No |
| `roles/implementer/CONTEXT.md` | Add `## Review Summary` as a required section in the Output template: "5–10 lines: deviations from architecture, known gaps, specific concerns for the reviewer. This is the reviewer's primary input." | Reduces reviewer context load; makes the deviations table more prominent | No |
| `roles/reviewer/CONTEXT.md` | Change "Read each code file listed in the implementer's file manifest" to "Read the implementer's Review Summary section first. Load files flagged there, plus all router/handler/endpoint files. Read shared utilities only if a finding requires it." | Reduces unnecessary file reads on large projects | No |

---

## One Change to Make Now

**Update `resources/typescript-conventions.md` with the TypeScript 6 breaking changes.**

Add a `## Known TypeScript 6 Breaking Changes` subsection with two entries:
1. `baseUrl` with `moduleResolution: bundler` raises a hard TypeScript 6 error. Use `paths` alone — `baseUrl` is not needed when `moduleResolution` is `bundler`. Remove `baseUrl` from any tsconfig that uses bundler resolution.
2. `import { defineConfig } from 'vite'` does not include types for the `test:` config block used by vitest. Use `import { defineConfig } from 'vitest/config'` instead — it re-exports all vite config types and adds the `test:` block.

These are concrete, documented, and will prevent two avoidable detours in the next TypeScript project.

---

## Handoff

This output is for human review. No workspace files have been modified.

**Recommended actions (in priority order):**
1. Update `resources/typescript-conventions.md` — add the TS6 breaking changes subsection (highest value, no decision required, ~10 lines)
2. Update `resources/python-conventions.md` — add `extra="ignore"` pydantic-settings note (~3 lines)
3. Update `skills/setup-ts-pnpm.md` — add shadcn/ui interactivity note (~5 lines)
4. Add pre-role check convention to routing.md preamble (~3 lines)
5. Add step 0 (archive check) to all role CONTEXT.md process sections — defer until next time a role is opened for editing
6. Add `## Review Summary` to implementer CONTEXT.md output template — defer until next project

**Update `_config/project-state.md`** to record that the retro ran on 2026-06-01 and which recommendations were actioned.
