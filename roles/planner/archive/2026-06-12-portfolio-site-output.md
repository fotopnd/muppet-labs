# Planner Output — portfolio-site

**Role:** planner  
**Sequence:** new-project-full  
**Step:** 2 of 9  
**Date:** 2026-06-12

---

## Project

**portfolio-site** — A static single-page marketing site presenting the Anthropic Safeguards portfolio as a three-project argument (Build → Attack → Measure), with key metrics, project cards, and links to deployed live demos.

---

## Requirements

1. The page renders a hero section with a headline framing the "Build → Attack → Measure" narrative and a single CTA anchor-scrolling to the projects section.
2. Three `ProjectCard` components render in a responsive grid: 3-column on desktop (≥1024px), 1-column on mobile.
3. Each `ProjectCard` displays: project name, one-sentence description, a `MetricsTable` with hardcoded key metrics, and a demo link that renders as "Demo coming soon" when no URL is provided.
4. `MetricsTable` accepts a typed `rows` prop and renders metric name + value pairs; it does not fetch data.
5. A `BioSection` renders a brief professional bio situating the portfolio work relative to Anthropic Safeguards roles (SWE + DE).
6. A sticky minimal `NavBar` provides anchor links to `#projects` and `#about`.
7. All metric values are hardcoded in `src/data/projects.ts` — no API calls at runtime.
8. `pnpm build` produces a `dist/` folder with zero TypeScript errors and zero ESLint errors.
9. The site is fully responsive: no horizontal overflow at any viewport width; tested at 375px and 1440px.
10. No external analytics, tracking scripts, web fonts with third-party requests, or API calls are included.
11. `vitest` runs cleanly; at minimum `ProjectCard` and `MetricsTable` have component tests.

---

## Technology Stack

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | TypeScript 5.x | Strict mode; consistent with all existing projects |
| UI library | React 19 | Functional components, hooks; no SSR needed |
| Bundler | Vite 6 | Fast dev server; `pnpm build` → `dist/` static output |
| Styling | Tailwind v4 | CSS-first `@theme` block; consistent with red-team-platform and error-hide-seek |
| Package manager | pnpm | Workspace standard |
| Formatter | prettier | Single config, enforced via script |
| Linter | eslint (flat config, `eslint.config.ts`) | typescript-eslint + react-hooks plugin |
| Testing | vitest + @testing-library/react | Colocated component tests; jsdom environment |
| Router | none | Single-page with anchor scroll; no route segments needed |
| Data fetching | none | All content is hardcoded static data |

---

## File and Module Structure

```
projects/portfolio-site/
├── index.html                    Vite entry point; sets page title and meta description
├── package.json                  Scripts: dev, build, preview, lint, test
├── pnpm-lock.yaml
├── vite.config.ts                Path alias @/ → src/; vitest config
├── tsconfig.json                 References app + node
├── tsconfig.app.json             Strict TS; moduleResolution bundler; @/* paths; no baseUrl
├── tsconfig.node.json            For vite.config.ts
├── eslint.config.ts              Flat config; typescript-eslint + react-hooks
├── .prettierrc                   semi:false, singleQuote:true, trailingComma:all, printWidth:100
├── .gitignore
└── src/
    ├── main.tsx                  React root; mounts App into #root
    ├── App.tsx                   Top-level layout: NavBar + main sections
    ├── index.css                 Tailwind v4 @import + @theme token block
    ├── data/
    │   └── projects.ts           Hardcoded project records (name, description, metrics, demoUrl)
    ├── components/
    │   ├── NavBar.tsx            Sticky minimal nav; anchor links to #projects and #about
    │   ├── HeroSection.tsx       Build → Attack → Measure headline; CTA button
    │   ├── ProjectCard.tsx       Card wrapper; renders name, description, MetricsTable, demo link
    │   ├── MetricsTable.tsx      Accepts MetricRow[]; renders name/value pairs in tabular style
    │   └── BioSection.tsx        Professional bio paragraph; situates work re: Anthropic Safeguards
    └── test/
        ├── setup.ts              @testing-library/jest-dom import
        ├── ProjectCard.test.tsx  Renders name, description, metric values, demo link behavior
        └── MetricsTable.test.tsx Renders all rows; handles empty rows prop
```

---

## Key Data Shape (for architect)

`src/data/projects.ts` exports an array of project records. The architect should define the exact types, but the shape is:

```ts
type MetricRow = { label: string; value: string }

type Project = {
  id: string
  name: string
  tagline: string
  description: string
  metrics: MetricRow[]
  demoUrl: string | null   // null → render "Demo coming soon"
}
```

The three records are:
- **LLM Safety Monitor** — metrics: Prompt F1 (0.818), Taxonomy macro-F1 (0.787), Pair F1 (0.549)
- **Red-Team Platform** — metrics: Attacks generated (1,797), Strategies covered (10), Avg ASR gap (architect to confirm format from SUMMARY.md)
- **Error Hide and Seek** — metrics: Uplift (Human+AI vs Human-only), n=110; architect to confirm exact metric labels from SUMMARY.md

---

## Open Questions for Architect

1. **Metrics exact values for Red-Team Platform and Error Hide and Seek** — the brief specifies "ASR split" and "uplift result" but doesn't give numeric values. Architect should read `projects/red-team-platform/SUMMARY.md` and `projects/error-hide-seek/SUMMARY.md` to extract the headline numbers before writing `projects.ts` data.  
   *Proposed answer:* Architect reads SUMMARY.md files and populates exact MetricRow labels and values in the type definition.

2. **Color accent** — neutral slate-only vs. a 10% accent hue.  
   *Proposed answer:* Use amber-600 as primary accent (CTA button, active nav link, metric value text) — Anthropic-adjacent, readable on white at WCAG AA. 60% slate/white canvas, 30% slate structure, 10% amber-600 accent.

3. **Hero CTA behavior** — external link to GitHub/demo vs. anchor scroll to #projects.  
   *Proposed answer:* Anchor scroll to `#projects` — no external URL assumed at build time; avoids broken links.

4. **Font loading** — self-hosted font vs. system font stack.  
   *Proposed answer:* System font stack for body (SF Pro / Inter / Segoe UI sans-serif); system monospace (SF Mono / JetBrains Mono) for metric values in MetricsTable. No external font requests.

5. **Project grid layout on tablet (768–1023px)** — 2-column or 1-column?  
   *Proposed answer:* 1-column at <1024px, 3-column at ≥1024px. Tablet gets same readable single-column layout as mobile. Three equal-width cards at ≥1024px.

---

## Handoff

**Next role:** architect  
The architect reads this file to design component interfaces (prop types), the `projects.ts` data structure (with exact metric values from SUMMARY.md files), the Tailwind `@theme` token block, and the layout grid strategy. Open questions above each have a proposed answer — architect confirms or overrides.

The architect should also read `resources/design_style.md` (Marketing/Landing Page context) to apply the correct visual register: wide-column centered container, high-contrast typographic hero, 3-column asymmetric features list, 60/30/10 color rule with amber-600 accent.

After architect: `design-brief` + `frontend-architect` sequence applies (project has a frontend).
