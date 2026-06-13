# design_style.md — Global Visual Style Guide

> **STATUS: POPULATED**
> 
> This file is loaded by the `frontend-architect` role (while planning token structures, layouts, and component logic) and the `ui-reviewer` role (as an engineering and visual quality standard).
> When this file is empty or a stub, those roles calibrate on generic utility frameworks alone.

---

## How This File Is Used

The `design-brief` role reads the "By Interface Context" section to identify which context
applies to the current project before any UI planning begins.

The `frontend-architect` role reads this file in full before generating component specs,
token structures, or layout decisions. Any populated section acts as a strict, universal
constraint on implementation — the architect applies these rules, not generic UI templates.

The `ui-reviewer` role reads this file before evaluating a completed interface. Populated
rules are enforcement criteria — if a layout or style choice violates a rule, it is flagged
as a violation with a specific fix required.

The `ui-debugger` role reads this file to verify that each fix it applies satisfies the
cited rule, and does not introduce new violations in adjacent code.

All four roles apply the rules that are filled in and ignore sections that remain empty.
No role invents layout or brand rules from this file's structure.

> **Component Scope:** Default is modular, encapsulated, utility-first component composition (Tailwind CSS primitives combined with semantic HTML). Custom arbitrary values in utility classes are not used.

---

## Design Principles

- **The Purposeful Workspace:** The visual design is clean, intentional, and highly organized, focusing on maximum data density without creating cognitive overload. It avoids superficial decorations, heavy gradients, or unnecessary animations, favoring functional clarity and crisp geometric boundaries.
- **Systematic, Not Dynamic:** The interface relies on a strict mathematical layout grid and unified spacing scales. Component design should invite user interaction through clear structural hierarchy rather than relying on aggressive hover animations or distracting micro-interactions.
- **Economy of Elements:** The layout register is professional web application, not experimental landing page. Every pixel, border, and background layer must earn its place. Comprehensive grid systems and unified flexbox structures are used to align content efficiently, avoiding arbitrary absolute positioning or manual padding hacks. If a visual element can be removed without losing layout structure, remove it.
- **Function-First Presentation:** Lead with critical content, core interactive elements, or primary data states immediately, establishing the functional utility baseline upfront. The exception: if the user requires complex setup context, front-load essential structural layout frameworks before rendering advanced sub-components.

---

## Layout and Rhythm

- **Unified Grid Structure:** Layouts lean toward comprehensive grid alignments that map spacing, responsive breakpoints, and information hierarchy within a single cohesive viewport strategy. The goal is geometric precision and layout efficiency, utilizing standardized layouts (such as explicit 12-column grids) rather than nesting disparate flexbox containers arbitrarily.
- **Predictable Visual Flow:** Rely heavily on explicit structural lines, consistent borders, and uniform vertical margins to guide the user's eye through dense information paths. Use layout anchors such as cards, explicit headers, defined sidebars, and explicit dividing sections.
- **Subtle Contrast Over Heavy Shapes:** When creating visual separation between neighboring blocks of content, prefer subtle background tint shifts over thick solid borders. Light background variations maintain a clean, sophisticated workspace feel, whereas heavy solid lines read as harsh and disruptive in this interface tier.
- **Punctuation Constraints (CSS/HTML):**
    - **Strictly Banned:** Never use arbitrary pixel spacing values (e.g., `h-[13px]`, `w-[342px]`) or inline style overrides (`style=""`).
    - **Preferred Alternative:** Achieve layout variations, depth, and distinct structural groupings exclusively through standardized Tailwind spacing scales (`space-y-4`, `p-6`), native CSS variables, and predefined theme configuration tokens.

---

## Typography & Color Choices

- **Token Discipline:** Every color value and font family definition must be explicitly mapped to a semantic design system token or CSS variable before being implemented in the code to ensure baseline scalability.
- **Font Pairing Hierarchy:** Limit the system to two distinct typeface roles to maintain clean visual rhythm:
    - **Primary Interface & Body:** A highly legible, neutral sans-serif (e.g., Inter, SF Pro, or Geist Sans) configured with tight tracking for interface density.
    - **Data & Code:** A crisp, clean monospace font (e.g., SF Mono, JetBrains Mono, or Geist Mono) utilized for all technical metadata, metrics, and tabular data blocks.
- **Strategic Hues for State:** When proposing or documenting an interactive state, lean into using an explicit color system intentionally (such as slate for neutral states, emerald for success, and amber for warnings) to foster immediate visual recognition and establish the color behavior as a discrete, predictable system object.
- **Banned Constructions:** Do not use vibrant neon primary colors, complex multi-stop background gradients, decorative script fonts, or more than one font family within a single text container to glue layout concepts together. Break information into clean, high-contrast text strings separated by uniform whitespace or subtle neutral dividers.

---

## Color Derivation & Palette Transformation

> **The Transposition Rule:** Do not anchor layouts to specific hardcoded color hues (e.g., "blue-600"). Instead, anchor layouts to **functional roles** using a standardized numeric weight scale (typically 50–950). If the base accent hue changes (e.g., from Blue to Orange), the agent must map the roles 1:1 across the new hue's scale to preserve contrast and readability.

### 1. Functional Mapping Matrix
When shifting color palettes, the agent must translate the color roles strictly according to this utility matrix:

| Functional Role | Default Scale (Blue Base) | Transposed Scale (Orange Example) | UI Application |
| :--- | :--- | :--- | :--- |
| **App Background** | Slate 50 / Zinc 950 | Slate 50 / Zinc 950 | Global viewport background canvas |
| **Surface / Card** | White / Slate 900 | White / Slate 900 | Content containers, tables, sidebars |
| **Muted Boundary** | Slate 200 / Slate 800 | Slate 200 / Slate 800 | Subtle dividers, low-contrast borders |
| **Primary Accent** | **Blue 600** / **Blue 500** | **Orange 600** / **Orange 500** | Primary buttons, active navigation states |
| **Accent Subtle** | **Blue 50** / **Blue 950** | **Orange 50** / **Orange 950** | Table row highlights, selected card backgrounds |
| **Text Intense** | Slate 900 / Slate 50 | Slate 900 / Slate 50 | Primary headers and high-priority copy |

### 2. Cyclic Pattern & Contrast Rules
- **Contrast Preservation:** The agent must ensure that any swapped accent color maintains an identical contrast ratio against the surface layer. If a primary action uses a `600` weight in Blue for WCAG AA compliance on a white background, it *must* use a `600` (or the equivalent contrast-matched weight) in Orange.
- **The 60-30-10 Rule:** The layout must strictly allocate color density to prevent vibrant hues from causing eye strain in professional environments:
    - **60% Canvas:** Dominated by the neutral background and surface tones (Slate/Zinc).
    - **30% Structure:** Dominated by text structural tones, borders, and passive UI boundaries.
    - **10% Accent:** Reserved exclusively for focal points, interactive triggers, and status anchors using the active accent hue (Blue, Orange, etc.).

---

## By Interface Context

> The base design tokens stay consistent across contexts. What changes is visual data density and layout complexity.

### Application Dashboard

- **Focus:** High data density, performance tracking, operational views, and system primitives.
- **Example Style:** *"A multi-pane layout featuring a sticky, low-contrast sidebar navigation, a clean monospace data table with explicit row heights, and subtle background highlights on active table states."*

### Technical Documentation

- **Focus:** Deep reading layout, clean typography hierarchy, scannability, and structural code blocks. Maintain layout credibility while explicitly detailing code snippets, utilizing high-contrast monospace text strings, and providing wide margins for comfortable long-form reading.
- **Example Style:** *"A split-pane framework pairing an asymmetric left-hand navigation list with a wide center text column, utilizing distinct top borders for code blocks to segment example snippets."*

### Marketing / Landing Page

- **Focus:** Clear value metrics, broad spacing layouts, and rapid conversion pathways. Strip away dense multi-pane data grids and focus on large typographic elements, generous whitespace allocations, and distinct structural container widths.
- **Example Style:** *"A centered, wide-column container featuring a high-contrast typographical hero block, an asymmetric 3-column features list, and a single prominent interactive call-to-action button."*

---

## Canonical Token Specification

All new and updated frontend projects use Tailwind v4 (`@tailwindcss/vite`) with an `@theme {}` block in `src/index.css`. Token names below are **canonical** — use them exactly. No project should invent alternatives.

### Required tokens

| Token | Semantic role | Tailwind utility |
|-------|--------------|-----------------|
| `--color-canvas` | Page / viewport background | `bg-canvas` |
| `--color-surface` | Card, panel, modal background | `bg-surface` |
| `--color-surface-muted` | Inset sections, metrics tables, code blocks | `bg-surface-muted` |
| `--color-border` | Dividers, input borders, table lines | `border-border` |
| `--color-text-primary` | Headings, labels, high-priority copy | `text-text-primary` |
| `--color-text-secondary` | Body text, descriptions | `text-text-secondary` |
| `--color-text-muted` | Timestamps, hints, tertiary metadata | `text-text-muted` |
| `--color-text-inverse` | Text rendered on accent-coloured backgrounds | `text-text-inverse` |
| `--color-accent` | Primary interactive colour — buttons, active nav, focus rings | `text-accent`, `bg-accent`, `border-accent` |
| `--color-accent-hover` | Hover variant of accent | `hover:text-accent-hover` |
| `--color-accent-subtle` | Accent background tints — row highlights, pill backgrounds | `bg-accent-subtle` |
| `--color-success` | Positive state badges, pass indicators | `text-success`, `bg-success` |
| `--color-warning` | Cautionary / degraded states | `text-warning` |
| `--color-danger` | Error, destructive, fail states | `text-danger` |
| `--font-sans` | All interface and body text | `font-sans` |
| `--font-mono` | Metrics, IDs, code, CLI snippets | `font-mono` |

**Values:** Use OKLCH for all colour tokens (resilient to P3/sRGB display differences and easy to adjust lightness without hue shift). Anchor to the 60-30-10 rule: canvas+surface = 60%, text+borders = 30%, accent family = 10%.

**Accent hue is per-project** — portfolio-site uses amber, error-hide-seek uses blue, red-team-platform uses purple. The token names are the same; only the OKLCH values differ.

### Alignment status of existing projects

| Project | Status | Non-canonical names in use |
|---------|--------|-----------------------------|
| portfolio-site | ✓ Canonical | — |
| error-hide-seek | Partial — rename needed | `--color-background` → `--color-canvas`; `--color-text-intense` → `--color-text-primary`; `--color-text-default` → `--color-text-secondary`; `--font-interface` → `--font-sans`; `--font-data` → `--font-mono` |
| red-team-platform | Pre-Tailwind — raw CSS vars | `--bg`, `--text`, `--text-h`, `--border`, `--accent`, `--mono`. Existing tabs keep these; new components (BiasHeatmap and later) use canonical `@theme` tokens added alongside existing CSS. |

### Feature-specific extension tokens

Projects may add semantic extension tokens for domain-specific states. Extension tokens must follow the `--color-[domain]-[role]` pattern and be defined in the `@theme` block. Example for bias divergence heatmap cells:

```css
--color-divergence-low:  /* 0.00–0.14 cosine distance */
--color-divergence-mid:  /* 0.15–0.34 */
--color-divergence-high: /* 0.35+     */
```

---

## What to Avoid

- **The "Trendy" Landing-Page Trap:** Avoid overly large typography, chaotic asymmetrical overlapping layers, or aggressive floating elements that disrupt the functional content flow.
- **Over-Decoration:** Do not present components without clear structural boundaries. Show the layout logic, invite clean navigation, and acknowledge explicit alignment. A user interacting with the page should be able to follow the data flow effortlessly without feeling overwhelmed by visual clutter.
- **Hard-Coded Styling:** Never use raw, unmapped color hex codes or unique arbitrary sizing values without anchoring their definitions within the primary theme configuration file.
- **Spacing Slippage:** Ensure no non-standard padding, margins, or inline style overrides slip into component markups. Watch for them especially in complex multi-column layouts where the temptation to manually shift elements with arbitrary pixel margins is highest.
- **Harsh Borders as a Separator:** Replace solid dark borders with subtle neutral background tints or restructure layout whitespace. Thick solid borders read as harsh and break the clean application register.