# Design Brief Output — portfolio-site

**Role:** design-brief  
**Sequence:** new-project-full (step 4)  
**Date:** 2026-06-12

---

## Interface Context

**Marketing / Landing Page**

This is a read-only, single-scroll persuasion surface — no data entry, no persistent state, no operational controls. The user arrives to form an impression of the portfolio, not to interact with a system. That maps exactly to the Marketing/Landing Page context from `design_style.md`: "clear value metrics, broad spacing layouts, and rapid conversion pathways... large typographic elements, generous whitespace allocations."

The project cards contain a small metrics table, which borrows from the Application Dashboard context — but only as a sub-component. The dominant register is marketing.

---

## Primary Interaction

**A visitor reads the three project cards and follows the demo link (or notes "coming soon") for the project that interests them most.**

Everything else on the page — the hero, the bio, the metrics — supports this. The card + demo-link pair is the unit of conversion.

---

## Key Visual Components

1. **`HeroSection`** — Full-width typographic block with eyebrow label, `<h1>` headline, subheadline, and a single CTA anchor button. Sets the "Build → Attack → Measure" frame before any project detail appears.

2. **`ProjectCard`** — Card container (bordered, no shadow) holding project name, tagline, `MetricsTable`, description paragraph, and a conditional demo link / "coming soon" span at the bottom. This is the primary content unit.

3. **`MetricsTable`** — Definition-list table inside each card showing 3–4 metric label/value pairs. Values in monospace; labels in muted text. Visually differentiates numbers from prose without leaving the card.

4. **`NavBar`** — Sticky minimal header: site title on the left, two anchor links on the right. Keeps the visitor oriented during scroll without dominating the viewport.

5. **`BioSection`** — Muted-background closing section with two short paragraphs: professional background, then why this portfolio was built. No metrics, no links — pure text.

---

## Done Criteria

1. Hero `<h1>` text is visible above the fold at both 375px and 1440px viewport widths with no horizontal overflow.
2. CTA button scrolls the page to `#projects` when clicked; button uses amber-600 background with legible white text.
3. Three project cards render in a 3-column grid at ≥1024px and a single column at 375px — no card overflow or truncation at either width.
4. Each card's `MetricsTable` renders all 4 metric rows with label text in muted/secondary color and value text in monospace.
5. All three cards currently show "Demo coming soon" (italic, muted) — not a broken link or an empty element.
6. `NavBar` is sticky: it remains visible at the top of the viewport after scrolling past the hero.
7. `BioSection` renders with a visually distinct background (surface-muted) that separates it from the projects section without a harsh border.
8. `pnpm build` exits 0 with zero TS errors and zero lint errors.
9. `pnpm test` exits 0 with all `ProjectCard` and `MetricsTable` tests passing.
10. No horizontal scrollbar appears at any viewport width between 375px and 1440px.

---

## Handoff

The frontend-architect reads this file alongside `roles/architect/output/output.md` and `resources/design_style.md`.

The architect output already contains full component interfaces, the Tailwind `@theme` token block, the `projects.ts` data spec, and layout class strings. The frontend-architect's job is to:
- Validate those specs against the done criteria above
- Confirm or adjust the layout grid and spacing rhythm
- Specify any interactive states not yet covered (hover on cards, active nav link on scroll)
- Produce the frontend-architect output the implementer executes from

Open decisions for frontend-architect:
- Whether `ProjectCard` gets a subtle hover state (e.g. border color lifts to amber-200) — the architect spec omits this
- Whether the `NavBar` active link highlights on scroll position (requires `IntersectionObserver`) or is purely static anchor links — static is simpler and sufficient for a portfolio
