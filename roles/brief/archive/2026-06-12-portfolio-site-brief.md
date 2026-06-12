# Brief — Portfolio Landing Site

**Sequence:** `new-project-full` | **Role:** brief | **Step:** 1 of N  
**Date:** 2026-06-12

---

## Project Name

portfolio-site

---

## Description

A static single-page marketing site that presents the Anthropic Safeguards portfolio as a coherent three-project argument — build the detector, attack it, measure the human layer — with key metrics, project cards, and links to deployed live demos.

---

## Language(s)

TypeScript (React, Vite, Tailwind)

---

## Success Criteria

1. Site renders a hero section framing the Build → Attack → Measure narrative
2. Three project cards: LLM Safety Monitor, Red-Team Platform, Error Hide and Seek — each showing its key metric (classifier F1 table, ASR split, uplift result)
3. Each card links to the deployed live demo URL
4. A brief bio/context section situates the work relative to Anthropic Safeguards
5. Site is fully static (`pnpm build` produces a `dist/`) — no server-side rendering, no API calls
6. Deploys as nginx-served static files on the same Hetzner CX33 as the project stack
7. Responsive on desktop and mobile
8. `pnpm build` clean (zero TypeScript errors, zero lint errors)

---

## Constraints

- Static only — no backend, no database, no API calls at runtime
- Must deploy as a `dist/` folder served by nginx; no Node.js process in production
- Tailwind v4 (consistent with existing projects)
- No external analytics or tracking scripts
- All metric numbers are hardcoded from the findings files — no live API fetching

---

## Out of Scope

- Unified dashboard aggregating live data from all projects
- Authentication or access control
- Blog / writing section
- Contact form
- Dark mode toggle
- Animations beyond simple CSS transitions

---

## Assumptions

- Live demo URLs will be known before the site is deployed (Hetzner deployment must come first or simultaneously)
- If demos are not yet live at deploy time, cards will show "demo coming soon" placeholder links
- Site will live at a subdomain or path on the Hetzner box (e.g. `safeguards.dev` or `<ip>/portfolio`)

---

## Handoff

Next role: planner  
The planner should decide: single-page with scroll sections vs multi-page with routing; whether to reuse shadcn/ui or raw Tailwind; exact component breakdown for the metrics tables. Confirm the demo URL strategy (placeholder vs live) before the architect proceeds.
