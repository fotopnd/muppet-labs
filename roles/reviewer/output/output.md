# Reviewer Output — portfolio-site

**Role:** reviewer  
**Sequence:** new-project-full (step 8)  
**Date:** 2026-06-12

---

## Summary

Clean static site with no logic errors and correct TypeScript throughout. Two minor items worth a quick fix before deploy: `githubUrl` is typed but never rendered (dead field), and `mt-auto` on the demo area `<div>` is a no-op given the sibling `grow`. No blocking issues. PASS WITH NOTES.

---

## Correctness

**C1 — Minor:** `ProjectCard.tsx:15` — `mt-auto` on the demo area `<div>` is unreachable. The description `<p>` at line 14 has `grow`, which expands to fill all remaining flex space, leaving zero margin for `mt-auto` to consume. The card layout renders correctly because `grow` handles the pushing — `mt-auto` is harmless but misleading.

**C2 — Minor:** `src/data/projects.ts:12` — `githubUrl: string | null` is defined on the `Project` type and set to `null` on all three entries, but nothing in the UI reads or renders it. `ProjectCard.tsx` only accesses `demoUrl`. Either render it (a GitHub link alongside the demo link) or remove it from the type until it's needed. As-is it creates a typed field with no behaviour.

**C3 — Minor:** `MetricsTable.tsx:15` — `key={row.label}` assumes metric labels are unique within a card. They are in the current `PROJECTS` data, but the type does not enforce uniqueness. If a duplicate label were added, React would warn silently (no crash, but potential reconciliation bugs). Acceptable given the data is hardcoded and controlled; note it for when dynamic data is ever added.

No logic errors, no unhandled nulls, no type-unsafe narrowing, no missing error paths (not applicable — no I/O).

---

## Style

**S1 — Minor:** `ProjectCard.tsx` — the `"View Demo →"` link text includes a raw `→` Unicode arrow. Screen readers will vocalise "View Demo right-pointing arrow" or similar. A `aria-label="View Demo"` on the `<a>` would give screen readers clean text while keeping the visual arrow. `typescript-conventions.md` §Accessibility note: "demo link gets `aria-label` if link text is generic" — the arrow makes this apply.

All other conventions clean:
- `import type` used on every type-only import ✓
- No `any`, no `!` assertions, no `ts-ignore` ✓
- `verbatimModuleSyntax` respected throughout ✓
- `SCREAMING_SNAKE_CASE` on `PROJECTS` module-level constant ✓
- `PascalCase.tsx` components, `kebab-case.ts` for data module ✓
- Props typed as inline `type` (not `interface`) ✓
- No non-null assertions in JSX ✓

---

## Tests

**T1 — Minor:** `ProjectCard.test.tsx` — no test for the description field. The five existing tests cover name, tagline, metric labels, and both demo states — adequate for the component's logic branches. Description is pure presentational text; testing it would verify the data layer not the component. Low value; not blocking.

**T2 — Minor:** No tests for `HeroSection`, `NavBar`, `BioSection`, or `ProjectsSection`. All four are pure-presentational with no conditional logic or branching. The implementer contract required only `ProjectCard` and `MetricsTable` tests. Adequate for a static portfolio. If `githubUrl` rendering is added to `ProjectCard`, a test for that branch should be added at the same time.

**T3 — Note:** The `baseProject` fixture in `ProjectCard.test.tsx` sets `githubUrl: null` to satisfy the `Project` type. When `githubUrl` is eventually used in the UI, the test file will need a corresponding branch test added.

---

## Refactor Candidates

**R1:** Remove `mt-auto` from `ProjectCard.tsx:15`. The `grow` on the description `<p>` is sufficient to anchor the demo area to the card bottom. `mt-auto` adds confusion without adding behaviour.

**R2:** Either render `githubUrl` in `ProjectCard` (a secondary link in the demo area row alongside or beneath `demoUrl`) or remove it from the `Project` type. A typed-but-unused field is silent maintenance noise; both resolutions are acceptable before deploy.

---

## Verdict

**PASS WITH NOTES**

C1 and C2 are the priority fixes before deploy. C1 (`mt-auto` removal) is a one-line change. C2 (`githubUrl`) is a design decision — render or remove. S1 (`aria-label` on demo link) is a good-citizenship fix, also one line.

---

## Handoff

Next role: retro (step 9)  
The retro reads this output alongside `implementer/output.md` and `project-state.md` to identify workspace improvements. The three open items above (C1, C2, S1) can be addressed in a quick implementer fixup pass if the human prefers clean code before deploy, or deferred until Hetzner URLs are added (at which point `githubUrl` rendering becomes relevant anyway).
