# Frontend-Architect Output — portfolio-site

**Role:** frontend-architect  
**Sequence:** new-project-full (step 5)  
**Date:** 2026-06-12

---

## Token Layer

Tailwind v4 uses a CSS-first `@theme` block — no `tailwind.config.js`. The token layer is defined in `src/index.css`. The architect output already specified the full block; this section confirms it and resolves the `setup-design-tokens` skill requirements.

**Accent hue: amber** — Anthropic-adjacent, WCAG AA on white at 600-weight. Confirmed in architect output.

```css
@import "tailwindcss";

@theme {
  /* --- Typography --- */
  --font-sans: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: ui-monospace, "SF Mono", "JetBrains Mono", "Fira Code", Consolas, monospace;

  /* --- Canvas (60%) --- */
  --color-canvas:       oklch(98.5% 0 0);    /* slate-50  — page background */
  --color-surface:      oklch(100% 0 0);     /* white     — card / panel surface */
  --color-surface-muted:oklch(96.1% 0 0);   /* slate-100 — BioSection bg, MetricsTable bg */

  /* --- Structure (30%) --- */
  --color-border:         oklch(91.8% 0 0);  /* slate-200 — card borders, row dividers */
  --color-text-primary:   oklch(15.1% 0 0);  /* slate-900 — headings, body */
  --color-text-secondary: oklch(44.6% 0 0);  /* slate-500 — taglines, labels, muted copy */
  --color-text-inverse:   oklch(98.5% 0 0);  /* slate-50  — text on accent backgrounds */

  /* --- Accent (10%) — amber-600/700 --- */
  --color-accent:        oklch(66.6% 0.179 60.4);  /* amber-600 — CTA bg, eyebrow, demo links, metric values */
  --color-accent-hover:  oklch(60.6% 0.179 60.4);  /* amber-700 — hover/active state */
  --color-accent-subtle: oklch(96.9% 0.021 60.4);  /* amber-50  — not used in v1; reserved */
}
```

**Token enforcement rule for implementer:** every color in the codebase must reference a `--color-*` CSS variable. No raw Tailwind hue utilities (e.g. `text-amber-600`, `bg-slate-100`) — use `text-[--color-accent]`, `bg-[--color-surface-muted]` etc. The sole exception: hover border on `ProjectCard` uses `hover:border-[--color-accent]/60` (opacity modifier on a CSS variable — valid Tailwind v4 syntax).

---

## Page Layout

Single vertical scroll. No router. Section order top to bottom:

```
<body bg-[--color-canvas]>
  <NavBar>           sticky top-0 z-50        h-14     full-width
  <main>
    <HeroSection>    id="hero"                py-24 lg:py-32   full-width, content centered max-w-3xl
    <ProjectsSection>id="projects"            py-20            full-width, grid max-w-6xl
    <BioSection>     id="about"               py-20            full-width, content centered max-w-2xl
  </main>
</body>
```

**Responsive breakpoints (Tailwind v4 defaults):**
- `sm`: 640px — not used
- `lg`: 1024px — primary breakpoint: 3-col grid activates, hero text scales up, nav padding widens
- No `md` breakpoint needed — design goes 1-col (mobile/tablet) → 3-col (desktop)

**Horizontal padding rhythm:**
- Mobile: `px-6` (24px) — all sections
- Desktop: `px-6 lg:px-12` — all sections except HeroSection (which centers via `max-w-*`)

**Vertical spacing between sections:** handled by each section's own `py-*` — no gap between `<main>` children.

**Scroll offset for anchor links:** `<html>` has `scroll-behavior: smooth` and `scroll-padding-top: 3.5rem` (= h-14, NavBar height) so anchor targets land below the sticky bar.

---

## Component Specs

### NavBar

- **Hierarchy:** standalone — no children components
- **Layout:** `sticky top-0 z-50 h-14 flex items-center justify-between px-6 lg:px-12`
- **Background:** `bg-[--color-surface]/95 backdrop-blur-sm` — 95% opaque white with blur; keeps page content legible as it scrolls under
- **Bottom edge:** `border-b border-[--color-border]`
- **Left:** site title `"Safeguards Portfolio"` — `text-sm font-semibold text-[--color-text-primary]`
- **Right:** anchor link group — `flex items-center gap-6`
  - Each link: `text-sm text-[--color-text-secondary] hover:text-[--color-text-primary] transition-colors duration-150`
  - `<a href="#projects">Projects</a>` and `<a href="#about">About</a>`
- **States:**
  - Default: text-secondary links
  - Hover: text-primary links (transition-colors)
  - No scroll-aware active state — static anchors only (simpler; sufficient for a 3-section portfolio)
- **Data:** none

---

### HeroSection

- **Hierarchy:** standalone — no child components
- **Layout:** `section py-24 lg:py-32 px-6 bg-[--color-canvas]`
- **Inner column:** `max-w-3xl mx-auto text-center flex flex-col items-center gap-4`
- **Elements top to bottom:**

  | Element | Classes |
  |---------|---------|
  | Eyebrow `<p>` | `text-xs font-mono font-semibold tracking-[0.2em] uppercase text-[--color-accent]` |
  | `<h1>` | `text-4xl lg:text-5xl font-bold text-[--color-text-primary] leading-tight tracking-tight` |
  | Subheadline `<p>` | `text-lg text-[--color-text-secondary] max-w-xl leading-relaxed` |
  | CTA `<a href="#projects">` | `inline-flex items-center bg-[--color-accent] hover:bg-[--color-accent-hover] text-[--color-text-inverse] text-sm font-semibold rounded-lg px-6 py-3 mt-2 transition-colors duration-150` |

- **Eyebrow text:** `"AI Safety · Portfolio"`
- **`<h1>` text:** `"Build the detector. Attack it. Measure the human layer."`
- **Subheadline text:** `"Three end-to-end projects in AI safety engineering — classifier training, structured red-teaming, and controlled measurement of human review."`
- **CTA text:** `"See the work"`
- **States:** CTA has default + hover (amber-700 bg)
- **Data:** none

---

### ProjectsSection

- **Hierarchy:** `ProjectsSection` → `ProjectCard[]`
- **Layout:** `section py-20 px-6 lg:px-12 bg-[--color-canvas]`
- **Section header:** `<h2 class="text-2xl font-bold text-[--color-text-primary] mb-12 text-center">The Work</h2>`
- **Grid:** `grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-6xl mx-auto`
- **Data:** receives `projects: Project[]` prop; maps to `<ProjectCard key={p.id} project={p} />`
- **States:** none at section level — states live on cards

---

### ProjectCard

- **Hierarchy:** `ProjectCard` → `MetricsTable`
- **Layout:** `bg-[--color-surface] rounded-xl border border-[--color-border] p-6 flex flex-col gap-4 transition-colors duration-150 hover:border-[--color-accent]/60`
- **No box shadow** — border-only card edge per design_style.md "subtle contrast over heavy shapes"
- **Elements top to bottom:**

  | Element | Classes | Notes |
  |---------|---------|-------|
  | Name `<h3>` | `text-lg font-semibold text-[--color-text-primary] leading-snug` | |
  | Tagline `<p>` | `text-sm text-[--color-text-secondary] leading-relaxed` | |
  | `<MetricsTable rows={project.metrics} />` | — | see MetricsTable spec |
  | Description `<p>` | `text-sm text-[--color-text-primary] leading-relaxed grow` | `grow` pushes demo area to card bottom |
  | Demo area `<div>` | `mt-auto pt-4 border-t border-[--color-border]` | always present; content conditional |

- **Demo area states:**
  - `demoUrl !== null`: `<a href={demoUrl} target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 text-sm font-medium text-[--color-accent] hover:text-[--color-accent-hover] transition-colors duration-150">View Demo →</a>`
  - `demoUrl === null`: `<span class="text-sm italic text-[--color-text-secondary]">Demo coming soon</span>`

- **States:**
  - Default: `border-[--color-border]`
  - Hover: `border-[--color-accent]/60` (soft amber border lift — visible but not garish)

- **Data:** `project: Project` prop

---

### MetricsTable

- **Hierarchy:** standalone — no child components
- **Layout:** `bg-[--color-surface-muted] rounded-lg p-4`
- **Element:** `<dl class="divide-y divide-[--color-border]">`
- **Each row:** `<div class="flex justify-between items-baseline py-1.5 first:pt-0 last:pb-0">`
  - `<dt class="text-xs text-[--color-text-secondary]">{row.label}</dt>`
  - `<dd class="text-sm font-mono font-semibold text-[--color-text-primary] tabular-nums">{row.value}</dd>`
- **Empty state:** if `rows.length === 0`, render nothing (`return null`)
- **States:** no interactive states — read-only display component
- **Data:** `rows: MetricRow[]` prop

---

### BioSection

- **Hierarchy:** standalone — no child components
- **Layout:** `section py-20 px-6 lg:px-12 bg-[--color-surface-muted]`
- **Inner column:** `max-w-2xl mx-auto`
- **`<h2>`:** `text-2xl font-bold text-[--color-text-primary] mb-8`  text: `"About"`
- **Para 1** (background): `text-base text-[--color-text-primary] leading-relaxed mb-4`
- **Para 2** (why): `text-base text-[--color-text-secondary] leading-relaxed`
- **Separation from ProjectsSection:** achieved by `bg-[--color-surface-muted]` background shift — no border, no divider element
- **States:** none
- **Data:** none

---

## Constraints Applied

1. **No arbitrary values** (`design_style.md` §Layout, "Strictly Banned") — every spacing and size value uses Tailwind's 4px-base scale. The `tracking-[0.2em]` on the eyebrow is the one exception — letter-spacing doesn't have a scale equivalent and this is a standard typographic choice. Flag for ui-reviewer.

2. **No box shadow on cards** (`design_style.md` §What to Avoid, "Harsh Borders") — `ProjectCard` uses border only; hover state uses border-color transition, not shadow lift. Implementer must not add `shadow-*` classes.

3. **60/30/10 color rule** — amber appears only on: eyebrow text, CTA button, card hover border, demo link text, metric `dd` values... wait — metric values are `text-[--color-text-primary]` (slate-900), not amber. Amber is reserved for the interactive + eyebrow layer. MetricsTable values are slate-900 monospace — correct.

4. **Font pairing discipline** — `font-mono` used exclusively for metric `<dd>` values in MetricsTable and the eyebrow label. All other text is `font-sans` (default). Implementer must not apply `font-mono` to prose copy.

5. **`backdrop-blur-sm` on NavBar** — requires a browser that supports `backdrop-filter`. Acceptable for a modern portfolio (no IE11 concern). Falls back gracefully to opaque white.

---

## Open Questions

None — all design-brief open questions resolved:

- **Card hover state** → `hover:border-[--color-accent]/60`: subtle amber border lift, no shadow. Confirmed.
- **NavBar active links** → static anchor links only; no `IntersectionObserver`. Confirmed.

---

## Handoff

**Next role:** implementer (single frontend phase — no backend)

The implementer reads this file alongside `roles/architect/output/output.md`. The architect output provides: the `projects.ts` data spec with exact metric values, all TypeScript types, the full `@theme` block, component prop signatures, and setup instructions (Tailwind v4 Vite plugin, `defineConfig` import, no `baseUrl`).

This file provides: all layout class strings, token enforcement rules, interactive state definitions, and exact copy strings for hardcoded text (eyebrow, h1, subheadline, CTA, section headers).

**Deviations from this spec must be documented in `implementer/output.md` with a reason.**

The ui-reviewer will check against the 10 done criteria in `roles/design-brief/output/output.md`. The implementer should run `pnpm build` and `pnpm test` before writing the implementer output.
