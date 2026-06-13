# Implementer Output — portfolio-site

**Role:** implementer  
**Sequence:** new-project-full (step 6 — single frontend phase)  
**Date:** 2026-06-12

---

## Phase

Single-language — TypeScript (React 19 + Vite 8 + Tailwind v4)

---

## Files Produced

| File | Purpose |
|------|---------|
| `index.html` | Page title "Safeguards Portfolio" + meta description |
| `vite.config.ts` | Tailwind v4 plugin, `@/` alias, vitest config (jsdom, globals, setup file) |
| `tsconfig.app.json` | Added strict, noUncheckedIndexedAccess, exactOptionalPropertyTypes, paths |
| `.prettierrc` | semi:false, singleQuote:true, trailingComma:all, printWidth:100 |
| `src/index.css` | Tailwind v4 `@import` + full `@theme` token block + html/body base styles |
| `src/main.tsx` | React entry; guard check replaces `!` non-null assertion |
| `src/App.tsx` | Top-level layout: NavBar + main sections + PROJECTS data injection |
| `src/data/projects.ts` | `MetricRow`, `Project` types + `PROJECTS` array with all metric values |
| `src/components/NavBar.tsx` | Sticky header; anchor links to #projects and #about |
| `src/components/HeroSection.tsx` | Eyebrow, h1, subheadline, CTA anchor button |
| `src/components/ProjectsSection.tsx` | Section heading + responsive 3-col grid; maps projects to cards |
| `src/components/ProjectCard.tsx` | Card with name, tagline, MetricsTable, description, demo area |
| `src/components/MetricsTable.tsx` | `<dl>` rows of label/value pairs; returns null on empty |
| `src/components/BioSection.tsx` | Two-paragraph About section; CV-grounded, no hiring-goal language |
| `src/test/setup.ts` | `@testing-library/jest-dom` setup |
| `src/test/ProjectCard.test.tsx` | 5 tests: name, tagline, metrics, demo-null, demo-set |
| `src/test/MetricsTable.test.tsx` | 2 tests: all rows render, empty array returns null |

---

## Setup Steps Taken

1. `pnpm create vite portfolio-site --template react-ts` — Vite 8 scaffold (react-ts)
2. `pnpm install`
3. `pnpm add -D tailwindcss @tailwindcss/vite`
4. `pnpm add -D vitest jsdom @testing-library/react @testing-library/user-event @testing-library/jest-dom prettier`
5. Added `"test": "vitest run"` script to `package.json`

The scaffold included `@eslint/js`, `typescript-eslint`, `eslint-plugin-react-hooks`, `@types/node`, and React 19 — no manual installation needed for those.

---

## Verification

```
pnpm build   → ✓ built in 64ms — 0 TS errors, 0 lint errors
pnpm lint    → ✓ 0 problems
pnpm test    → ✓ 2 test files, 7 tests, all passed
```

---

## Deviations from Architecture

1. **Triple-slash reference removed from `vite.config.ts`** — `/// <reference types="vitest/config" />` was flagged by `@typescript-eslint/triple-slash-reference`. Removed; `defineConfig` from `vitest/config` provides the type inference without it. Build and tests still clean.

2. **Scaffold Vite version is 8 (not 6)** — `pnpm create vite` resolved to Vite 8.0.16. No API changes affect this project; `@tailwindcss/vite` 4.3.0 is compatible.

3. **Token utility class naming** — In Tailwind v4, `@theme` variables map to shorthand utilities: `--color-text-primary` → `text-text-primary`, `--color-surface-muted` → `bg-surface-muted`, etc. All class strings in the frontend-architect spec that used `bg-[--color-*]` / `text-[--color-*]` arbitrary syntax were replaced with the shorthand equivalents (`bg-canvas`, `text-text-primary`, `bg-surface-muted`, `border-border`). Behaviour is identical. Exception: `hover:border-accent/60` uses opacity modifier on the shorthand token — valid Tailwind v4 syntax.

4. **`eslint.config.js` kept as `.js`** — Scaffold generated `.js`; renaming to `.ts` would require additional tsconfig adjustments for the linter process. The typescript-conventions.md prefers `.ts` but the existing config is functionally equivalent. Left as-is.

---

## Known Gaps

- All three `demoUrl` and `githubUrl` values are `null` — "Demo coming soon" renders on every card. Update `src/data/projects.ts` when Hetzner deploy URLs are available.
- No `favicon.svg` replacement — the Vite scaffold's default favicon is in place.
- `App.css` from scaffold was not explicitly deleted (it is not imported anywhere and will not be bundled).

---

## How to Run

```bash
cd projects/portfolio-site
pnpm dev        # dev server at http://localhost:5173
pnpm build      # produces dist/
pnpm preview    # preview the dist/ build
pnpm test       # run vitest
pnpm lint       # run eslint
```

---

## Handoff

Next role: ui-reviewer (step 7)  
The ui-reviewer checks the 10 done criteria in `roles/design-brief/output/output.md` against the running site. Key areas to verify:
- 3-col grid at ≥1024px, 1-col at 375px — can be checked at viewport widths
- Sticky NavBar behaviour after scrolling past hero
- "Demo coming soon" italic muted text on all three cards
- MetricsTable monospace values, muted labels
- No horizontal overflow at 375px or 1440px
- `bg-surface-muted` background shift on BioSection (distinct from projects section without a border)

One flagged item from frontend-architect: `tracking-[0.2em]` on the eyebrow in HeroSection is the single arbitrary value in the codebase — no standard Tailwind scale equivalent for letter-spacing at this value.
