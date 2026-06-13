# Retro — red-team-platform dashboard refinement

**Role:** retro  
**Sequence:** existing-project-refinement (brief → planner → architect → implementer → reviewer)  
**Date:** 2026-06-13

---

## Project

`projects/red-team-platform/web/` — full dashboard refinement pass addressing 10 user-identified issues across 7 frontend pages + 3 new backend API endpoints.

---

## What Went Well

**W1 — Brief-to-impl fidelity.** All 10 brief items landed without scope drift. The architect's design decisions (single DB round-trip for summary, ORM vs text() split, 200-row dedup ceiling) were followed exactly.

**W2 — Ruff caught import + line-length issues proactively.** Running `uv run ruff check --fix` after each file cleaned I001 (import order) and flagged E501 (line > 100), which were then manually split. No ruff errors at reviewer pass.

**W3 — CoverageGrid CSS grid pattern is clean.** Replacing Recharts ScatterChart-as-grid with a plain CSS grid component removed ~80 lines of coordinate math and made tooltips trivial.

**W4 — categoryLabels.ts as single source of truth.** Zero raw `LABEL_N` strings in rendered output. Propagation via `labelName()` / `abbrevName()` / `categoryColour()` was clean across all pages.

---

## What Went Wrong / Friction Points

**F1 — asyncpg NULL parameter error (blocking).** The original `/attacks/summary` implementation used a `text()` CTE with `:source IS NULL OR source = :source`. This raised `AmbiguousParameterError` at runtime because asyncpg can't infer the type of `$1 IS NULL`. Required a full rewrite to ORM-based conditional `.where()` building. Cost: ~30 min. Root cause: the asyncpg extended protocol rule wasn't in workspace conventions, so the architect designed a valid SQL pattern that the driver can't execute.

**F2 — Static `style={{}}` on legend swatches (caught in review).** Three legend color indicators in `CoverageHeatmap.tsx` used `style={{ backgroundColor: 'hsl(120, 65%, 45%)' }}` — static literal values that should be Tailwind classes. This was a reviewer catch, not caught during implementation. The inline-style policy wasn't explicit enough about which cases are justified.

**F3 — Context compaction mid-session.** The reviewer pass was split across a context window boundary (limit hit). The next session resumed correctly from the summary, but the split added friction. No workspace action needed; inherent to long sessions.

---

## Workspace Updates Applied

| Resource | Change | Why |
|---|---|---|
| `resources/python-conventions.md` | Added **asyncpg NULL parameter rule** under SQLAlchemy section | F1 — prevent recurrence: use ORM when filters can be None; `text()` only when all params non-null |
| `resources/typescript-conventions.md` | Added **Inline Styles** section (justified vs unjustified cases) | F2 — explicit policy on when `style={{}}` is acceptable |
| `resources/typescript-conventions.md` | Added **Recharts Patterns** section (ScatterChart-as-grid anti-pattern, ZAxis bubble charts, LabelList SVG styling) | Captures patterns discovered during CoverageGrid and FailureClusters rewrites |

---

## Decision Log Entries to Add

| Decision | Reason |
|---|---|
| asyncpg NULL workaround: ORM over text() when filters can be None | asyncpg extended protocol raises AmbiguousParameterError on `$1 IS NULL`; ORM avoids passing None to any SQL parameter |
| Static legend swatches use Tailwind classes, not style={{}} | Legend colors are static literals, not dynamic computed values; Tailwind arbitrary values (`bg-[hsl(...)]`) or approximation classes are correct |

---

## Open Items Carried Forward

None. All 10 brief items shipped. Reviewer verdict PASS WITH NOTES (one pre-output fix applied; back-translation column is placeholder per brief scope).

---

## Handoff

Sequence complete. Next step: update `_config/project-state.md` to reflect retro completion, then git commit all new and modified files.
