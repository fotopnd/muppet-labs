# Architect Output — portfolio-site

**Role:** architect  
**Sequence:** new-project-full  
**Step:** 3 of 9  
**Date:** 2026-06-12

---

## System Overview

`portfolio-site` is a fully static React 19 + Vite 6 + Tailwind v4 single-page application. It has no runtime API calls, no router, and no server-side logic. The entire site is one scroll page composed of four sections: `NavBar` (sticky header with anchor links), `HeroSection` (headline + CTA), `ProjectsSection` (3-column grid of `ProjectCard`), and `BioSection` (professional context paragraph). All content — project names, descriptions, metric values, and demo URLs — is defined in a single `src/data/projects.ts` module and passed down as props. The `dist/` output is served directly by nginx with no Node.js process.

---

## Open Questions Resolved

| # | Question | Decision |
|---|----------|----------|
| 1 | Metric values for Red-Team Platform and Error Hide and Seek | Resolved below from SUMMARY.md files |
| 2 | Color accent | amber-600 as primary accent (10% rule); slate-900/50 for text; white/slate-50 surfaces |
| 3 | Hero CTA behavior | Anchor scroll to `#projects` |
| 4 | Font loading | System font stack only — no external font requests |
| 5 | Tablet grid (768–1023px) | 1-column below 1024px, 3-column at ≥1024px |

---

## Data Models

### `src/data/projects.ts`

```ts
export type MetricRow = {
  label: string   // e.g. "Prompt F1"
  value: string   // e.g. "0.818"
}

export type Project = {
  id: string           // slug, used as React key and aria-labelledby anchor
  name: string         // display name
  tagline: string      // one-sentence summary shown below the name
  description: string  // two-to-three sentence narrative paragraph in card body
  metrics: MetricRow[] // 3–4 rows; rendered by MetricsTable
  demoUrl: string | null  // null → render "Demo coming soon" (disabled link)
  githubUrl: string | null
}

export const PROJECTS: Project[] = [
  {
    id: 'llm-safety-monitor',
    name: 'LLM Safety Monitor',
    tagline: 'Fine-tuned classifiers that score production traffic for harmfulness, prompt injection, and taxonomy category in real time.',
    description:
      'Three RoBERTa-base classifiers trained on HH-RLHF and WildGuard data — one for pair-level harmfulness, one for prompt injection, one for 13-category harm taxonomy. The monitor streams live events through a Kafka pipeline and exposes a FastAPI metrics endpoint consumed by the moderation dashboard.',
    metrics: [
      { label: 'Prompt classifier F1', value: '0.818' },
      { label: 'Taxonomy macro-F1', value: '0.787' },
      { label: 'Pair classifier F1', value: '0.549' },
      { label: 'Training set', value: '50k pairs (HH-RLHF)' },
    ],
    demoUrl: null,
    githubUrl: null,
  },
  {
    id: 'red-team-platform',
    name: 'Red-Team Platform',
    tagline: 'Corpus-driven jailbreak campaigns with classifier scoring, semantic clustering, and live safety monitor integration.',
    description:
      'Runs structured attack campaigns against an Ollama-compatible model, scores every response with the shared safety classifier, clusters successful attacks by mechanism, and publishes all 1,797 events to the live monitor via Kafka outbox. A React dashboard surfaces attack-success-rate splits by strategy, semantic cluster breakdowns, and regression tracking across runs.',
    metrics: [
      { label: 'Attacks (Phase 1)', value: '1,797' },
      { label: 'Strategies tested', value: '6' },
      { label: 'Top ASR (few_shot_json)', value: '100%' },
      { label: 'Fully-resisted strategies', value: '3 of 6' },
    ],
    demoUrl: null,
    githubUrl: null,
  },
  {
    id: 'error-hide-seek',
    name: 'Error Hide and Seek',
    tagline: 'A randomised controlled trial measuring whether AI hints improve human detection of planted errors in academic abstracts.',
    description:
      'Two experiments across 100 papers and 67 human review sessions compared unaided detection against human+agent detection. Overall TPR uplift was −0.01 (null result). Category-level decomposition found +0.33 uplift for inverted-conclusion errors — the one category where Claude can reason without ground-truth access — and zero or negative uplift for domain-dependent categories.',
    metrics: [
      { label: 'Human+Agent TPR', value: '0.29' },
      { label: 'Unaided TPR', value: '0.30' },
      { label: 'Overall uplift', value: '−0.01' },
      { label: 'Inverted-conclusion uplift', value: '+0.33' },
    ],
    demoUrl: null,
    githubUrl: null,
  },
]
```

---

## Tailwind v4 Token Block (`src/index.css`)

```css
@import "tailwindcss";

@theme {
  /* Typography */
  --font-sans: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: ui-monospace, "SF Mono", "JetBrains Mono", "Fira Code", Consolas, monospace;

  /* Color roles — 60/30/10 rule */
  /* 60% canvas */
  --color-canvas: oklch(98.5% 0 0);        /* ~slate-50 */
  --color-surface: oklch(100% 0 0);        /* white */
  --color-surface-muted: oklch(96.1% 0 0); /* ~slate-100 */

  /* 30% structure */
  --color-border: oklch(91.8% 0 0);        /* ~slate-200 */
  --color-text-primary: oklch(15.1% 0 0);  /* ~slate-900 */
  --color-text-secondary: oklch(44.6% 0 0);/* ~slate-500 */
  --color-text-inverse: oklch(98.5% 0 0);  /* ~slate-50 */

  /* 10% accent — amber-600 */
  --color-accent: oklch(66.6% 0.179 60.4);       /* amber-600 */
  --color-accent-hover: oklch(60.6% 0.179 60.4); /* amber-700 */
  --color-accent-subtle: oklch(96.9% 0.021 60.4);/* amber-50 */
}
```

---

## Module Interfaces

### `src/data/projects.ts`
```ts
export type MetricRow = { label: string; value: string }
export type Project = { id, name, tagline, description, metrics, demoUrl, githubUrl }
export const PROJECTS: Project[]
```
No imports. Pure data. Consumed by `App.tsx` and `ProjectsSection`.

---

### `src/App.tsx`
```tsx
// No props — root component
export default function App(): JSX.Element
// Renders: <NavBar /> <main> <HeroSection /> <ProjectsSection projects={PROJECTS} /> <BioSection /> </main>
```

---

### `src/components/NavBar.tsx`
```tsx
// No props
export default function NavBar(): JSX.Element
// Sticky top-0 bar; z-50; white background with bottom border (border-[--color-border])
// Left: site title "Safeguards Portfolio" (slate-900, font-semibold)
// Right: two anchor links — "Projects" → #projects, "About" → #about
// Height: h-14; horizontal padding: px-6 lg:px-12
```

---

### `src/components/HeroSection.tsx`
```tsx
// No props
export default function HeroSection(): JSX.Element
// Full-width section; bg-[--color-canvas]; py-24 lg:py-32
// Centered column: max-w-3xl mx-auto px-6 text-center
// Elements:
//   <p> — eyebrow: "AI Safety · Anthropic Safeguards Portfolio" (amber-600, text-sm font-mono tracking-widest uppercase)
//   <h1> — "Build the detector. Attack it. Measure the human layer."
//          (text-4xl lg:text-5xl font-bold text-[--color-text-primary] leading-tight)
//   <p> — subheadline: 2-sentence description of the three-project argument
//          (text-lg text-[--color-text-secondary] mt-4 max-w-xl mx-auto)
//   <a href="#projects"> — CTA button:
//          bg-[--color-accent] hover:bg-[--color-accent-hover]
//          text-white font-semibold rounded-lg px-6 py-3 mt-8 inline-block
//          transition-colors duration-150
```

---

### `src/components/ProjectsSection.tsx`
```tsx
type ProjectsSectionProps = { projects: Project[] }
export default function ProjectsSection({ projects }: ProjectsSectionProps): JSX.Element
// id="projects"; bg-[--color-canvas]; py-20; px-6 lg:px-12
// Section header: <h2> "The Work" — text-2xl font-bold text-[--color-text-primary] mb-12 text-center
// Grid: grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-6xl mx-auto
// Renders: projects.map(p => <ProjectCard key={p.id} project={p} />)
```

---

### `src/components/ProjectCard.tsx`
```tsx
type ProjectCardProps = { project: Project }
export default function ProjectCard({ project }: ProjectCardProps): JSX.Element
// bg-[--color-surface]; rounded-xl; border border-[--color-border]; p-6; flex flex-col gap-4
// No shadow — uses border for card edge definition (design_style.md: subtle contrast over heavy shapes)
// Elements (top to bottom):
//   <h3> — project.name (text-lg font-semibold text-[--color-text-primary])
//   <p>  — project.tagline (text-sm text-[--color-text-secondary])
//   <MetricsTable rows={project.metrics} />
//   <p>  — project.description (text-sm text-[--color-text-primary] mt-auto leading-relaxed)
//   Demo link row (bottom): conditional on demoUrl
//     demoUrl !== null → <a href={demoUrl} target="_blank" rel="noopener noreferrer"> "View Demo →"
//                        (text-[--color-accent] hover:text-[--color-accent-hover] text-sm font-medium)
//     demoUrl === null  → <span> "Demo coming soon"
//                        (text-[--color-text-secondary] text-sm italic)
```

---

### `src/components/MetricsTable.tsx`
```tsx
type MetricsTableProps = { rows: MetricRow[] }
export default function MetricsTable({ rows }: MetricsTableProps): JSX.Element
// bg-[--color-surface-muted]; rounded-lg; p-4
// <dl> element — definition list for semantic label/value pairing
// Each row: <div class="flex justify-between items-baseline py-1 border-b border-[--color-border] last:border-0">
//   <dt> — row.label: text-xs text-[--color-text-secondary] font-sans
//   <dd> — row.value: text-sm font-mono font-semibold text-[--color-text-primary]
//                     (monospace for metric values per design_style.md typography rule)
// Empty rows prop → renders nothing (no error)
```

---

### `src/components/BioSection.tsx`
```tsx
// No props
export default function BioSection(): JSX.Element
// id="about"; bg-[--color-surface-muted]; py-20; px-6 lg:px-12
// Centered column: max-w-2xl mx-auto
// <h2> "About" — text-2xl font-bold text-[--color-text-primary] mb-6
// Two <p> blocks (hardcoded):
//   Para 1 — Professional background:
//     Data engineer at Meta London with ~14 years across data engineering,
//     analytics engineering, and business intelligence. Current focus:
//     account security and authentication analytics (Account Access and Recovery team).
//     Languages: Python, TypeScript, Rust.
//   Para 2 — Why this portfolio:
//     These projects came out of a sustained effort to build and evaluate
//     AI safety infrastructure hands-on — training classifiers, running structured
//     attack campaigns, and measuring the human review layer with a controlled experiment.
//     Each one is end-to-end: built, instrumented, and tested.
// No dynamic data. No hiring-goal language.
```

---

## Component Dependency Map

```
App.tsx
├── NavBar.tsx          (no deps)
├── HeroSection.tsx     (no deps)
├── ProjectsSection.tsx
│   └── ProjectCard.tsx
│       └── MetricsTable.tsx   (no deps)
└── BioSection.tsx      (no deps)

src/data/projects.ts → imported by App.tsx, passed as props down to ProjectCard/MetricsTable
```

No circular dependencies. Data flows strictly down from `projects.ts` → `App` → `ProjectsSection` → `ProjectCard` → `MetricsTable`.

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Error handling | None required — no runtime I/O, no async operations; TypeScript strict mode catches type errors at build time |
| Configuration | No `import.meta.env` usage — all content is hardcoded; `.env.example` is empty but present (tooling convention) |
| Logging | None — static site |
| Testing | Component tests with vitest + @testing-library/react; test `ProjectCard` renders name/tagline/metrics/demo states; test `MetricsTable` renders all rows and handles empty array |
| Accessibility | Use semantic HTML: `<nav>`, `<main>`, `<section>`, `<h1>`/`<h2>`/`<h3>` hierarchy, `<dl>`/`<dt>`/`<dd>` for metrics; anchor links with descriptive text; demo link gets `aria-label` if link text is generic |

---

## Implementation Notes for Implementer

1. **Tailwind v4 CSS-first setup.** The `@theme` block goes in `src/index.css`. No `tailwind.config.js`. Import with `@import "tailwindcss"` at the top, then `@theme { ... }`. Install via `pnpm add -D tailwindcss @tailwindcss/vite`. Add the Vite plugin to `vite.config.ts`:
   ```ts
   import tailwindcss from '@tailwindcss/vite'
   // in plugins: [react(), tailwindcss()]
   ```

2. **CSS variable usage in Tailwind v4.** Use `bg-[--color-canvas]` or `text-[--color-text-primary]` syntax to reference `@theme` variables in utility classes. This is the v4 pattern — no `theme()` function needed.

3. **No `baseUrl` in `tsconfig.app.json`.** TypeScript 6 deprecates it. Use `paths` alone with `moduleResolution: bundler` and add `"ignoreDeprecations": "6.0"` if scaffolded with `baseUrl`.

4. **`defineConfig` import for vitest.** Import from `'vitest/config'`, not `'vite'`, to get the `test:` block typed correctly.

5. **`pnpm build` verification.** After the implementer writes all files: `pnpm build` must exit 0 with zero TS errors; `pnpm lint` must exit 0; `pnpm test` must exit 0 with all tests passing.

6. **Project directory location.** Create at `projects/portfolio-site/` — consistent with all other projects in the workspace.

7. **Smooth scroll.** Add `html { scroll-behavior: smooth; }` to `index.css` for anchor link navigation.

8. **`index.html` meta tags.** Set `<title>Safeguards Portfolio</title>` and `<meta name="description" content="AI safety engineering portfolio: LLM classifier training, red-team attack platform, and human review measurement.">`.

9. **msw allowBuilds.** If msw is installed (it is not needed here — no API calls), the `pnpm-workspace.yaml` allowBuilds entry is required for pnpm v11. Since msw is not needed, do not install it.

10. **Test content.** `ProjectCard.test.tsx` must assert: project name renders, tagline renders, all metric labels render, demo link renders "View Demo →" when `demoUrl` is set and "Demo coming soon" when null. `MetricsTable.test.tsx` must assert: all `rows` render as label/value pairs, empty array renders nothing.

---

## Handoff

**Next role:** design-brief (per `new-project-full` step 4 — project has frontend)  
The design-brief role reads this file + `resources/design_style.md` to lock in the interface context (Marketing/Landing Page), primary interaction model (read-only scroll), key components (HeroSection, ProjectCard, MetricsTable), and done criteria before frontend-architect proceeds.

The design-brief should confirm the interface context is "Marketing / Landing Page" from `design_style.md` and that the amber-600 accent and system font stack decisions are carried forward. No open structural questions remain — all planner open questions are resolved above.

After design-brief → frontend-architect → implementer (single frontend phase, no backend).
