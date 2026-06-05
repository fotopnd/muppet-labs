# Planner Output — moderation-dashboard safety-signal additions

**Date:** 2026-06-05
**Sequence:** add-feature (additive pass on existing running project)
**Role executing:** planner

---

## Project

**moderation-dashboard-safety-signals** — Add live flag rate per model card and a model disagreement analysis panel to the moderation dashboard, surfacing distribution-shift and disagreement signals currently hidden in the database.

---

## Resolved Open Questions (from brief)

**Q1: Extend `_METRICS_SQL` with FILTER aggregates vs separate query for live counts?**
**Separate query.** `_METRICS_SQL` takes a `:group_filter` param and is called multiple times per request. Adding live count columns would require scoping them to shadow group inside a group-filtered query, which breaks the abstraction. A dedicated `_LIVE_COUNTS_SQL` runs once, filters `seeded=false` in the shadow group (which sees all live events), and returns per-model counts. `_build_model_metrics()` accepts live counts as a new parameter.

**Q2: Disagreement panel — inside ModelComparison tab, or new tab?**
**Inside ModelComparison tab.** Disagreement is inherently a comparison story. Adding a panel below the existing model cards grid keeps the concept co-located without adding navigation complexity. The tab already tells the shadow-group story; the panel extends it with the disagreement sub-story.

**Q3: `/metrics/disagreements` — pagination?**
**No pagination.** Fixed 10-sample window. The endpoint selects up to 50 recent disagreement escalations and returns 10. Sufficient for v1 portfolio context.

---

## Requirements

1. `ModelMetrics` schema has two new integer fields: `live_event_count` and `live_flagged_count`, populated by a dedicated SQL query (`seeded=false`, shadow group).
2. `/metrics/production`, `/metrics/shadow`, and `/metrics/all` all return `live_event_count` and `live_flagged_count` on every `ModelMetrics` object.
3. Each `ModelCard` renders a "Live: X.X% flagged" stat computed as `live_flagged_count / live_event_count`. When `live_event_count == 0`, the stat renders `—`.
4. The live flag rate stat is visible on all three model cards simultaneously without clicking or expanding anything.
5. `GET /metrics/disagreements` exists and returns: `total_last_hour: int`, `by_category: dict[str, int]`, and `samples: list` of up to 10 posts.
6. Each disagreement sample includes: `event_id`, `content` truncated to 140 chars, and `verdicts: list` of per-model `(model_name, predicted_label, confidence)`.
7. Disagreement samples are sourced only from `escalation_reason='model_disagreement'` rows in the shadow group.
8. A `DisagreementPanel` component renders below the model cards grid inside `ModelComparison`, showing total count, a category breakdown table, and the sample post list.
9. All existing Python tests pass (`uv run pytest`).
10. All existing frontend tests pass (`pnpm test`) and no new TypeScript errors are introduced.
11. At least one new Python test asserts that `/metrics/disagreements` returns correctly shaped data from seeded rows.
12. At least one new Python test asserts that `/metrics/all` (or `/metrics/production`) returns non-zero `live_event_count` and `live_flagged_count` when live rows exist in the shadow group.

---

## Technology Stack

| Concern | Choice | Reason |
|---------|--------|--------|
| Language — backend | Python 3.14 (existing) | Match project env |
| Package manager | uv (existing) | Workspace standard |
| Formatter/linter | ruff (existing) | Workspace standard |
| Web framework | FastAPI (existing) | Additive endpoint only |
| ORM / queries | SQLAlchemy async raw text (existing) | Consistent with all other queries in metrics.py |
| Schema validation | Pydantic v2 (existing) | Additive fields only |
| Language — frontend | TypeScript 5.x / React (existing) | Additive components only |
| Frontend build | Vite + pnpm (existing) | No change |
| Data fetching | TanStack Query (existing) | New hook follows same pattern as `useShadowMetrics` |
| Testing — backend | pytest (existing) | Additive tests in test_api.py |
| Testing — frontend | vitest + @testing-library/react (existing) | Additive tests in ModelComparison.test.tsx |

---

## File and Module Structure

This is an additive pass — no new directories. Changes touch the following files only:

### Backend

| File | Change |
|------|--------|
| `moderation_dashboard/api/schemas.py` | Add `live_event_count: int`, `live_flagged_count: int` to `ModelMetrics`; add `DisagreementVerdict`, `DisagreementSample`, `DisagreementsResponse` schemas |
| `moderation_dashboard/api/routers/metrics.py` | Add `_LIVE_COUNTS_SQL`; update `_build_model_metrics()` signature to accept live counts dict; add `GET /metrics/disagreements` with `_DISAGREEMENTS_TOTAL_SQL` and `_DISAGREEMENT_SAMPLES_SQL` |
| `tests/test_api.py` | Add 2 new tests: live count fields populated; disagreements endpoint shape |

### Frontend

| File | Change |
|------|--------|
| `web/src/types/index.ts` | Add `live_event_count: number`, `live_flagged_count: number` to `ModelMetrics` type; add `DisagreementVerdict`, `DisagreementSample`, `DisagreementsResponse` types |
| `web/src/api/shadow.ts` | Add `useDisagreements` hook (polls `/metrics/disagreements` every 30s via TanStack Query) |
| `web/src/components/ModelCard.tsx` | Add "Live: X.X% flagged" `MetricCell` to the existing stats grid |
| `web/src/components/DisagreementPanel.tsx` | New component — total count header, category breakdown table, sample post list |
| `web/src/pages/ModelComparison.tsx` | Import and render `<DisagreementPanel />` below the model cards grid |
| `web/src/test/ModelComparison.test.tsx` | Add tests: live flag rate stat renders; DisagreementPanel renders with mock data |

---

## Open Questions for Implementer

Two lookup questions to confirm during implementation (do not block on them):

1. **`escalation_reason` value** — confirm the string is exactly `'model_disagreement'` (not `'disagreement'`). Check `moderation_dashboard/escalation/service.py`.
2. **`predicted_label` range** — confirm it is strictly 0 or 1 for all three live models before using `SUM(predicted_label)` as a flagged count. If not, use `COUNT(*) FILTER (WHERE predicted_label = 1)` instead (safer).

---

## Handoff

Next role: implementer

The implementer reads this file and `roles/brief/output/output.md` for full context.

Files to read before starting:
- `moderation_dashboard/api/schemas.py` — current `ModelMetrics` shape
- `moderation_dashboard/api/routers/metrics.py` — existing `_METRICS_SQL`, `_build_model_metrics()`, endpoint patterns
- `moderation_dashboard/api/models.py` — ORM column names to confirm `seeded`, `group`, `predicted_label`
- `web/src/components/ModelCard.tsx` — where to add the live flag rate cell
- `web/src/pages/ModelComparison.tsx` — where to add `DisagreementPanel`
- `web/src/api/shadow.ts` — template for `useDisagreements` hook

Implementation order:
1. Backend schemas — add fields and new response types
2. Backend `_LIVE_COUNTS_SQL` + update `_build_model_metrics()` → verify with `curl /metrics/all`
3. Backend `GET /metrics/disagreements` → verify with `curl`
4. Backend tests — 2 new assertions in `test_api.py`; run `uv run pytest`
5. Frontend types — extend `ModelMetrics`, add disagreement types
6. Frontend `ModelCard` — add live flag rate stat; run `pnpm test`
7. Frontend `useDisagreements` hook + `DisagreementPanel` component
8. Frontend `ModelComparison` — wire in `DisagreementPanel`
9. Frontend tests — update `ModelComparison.test.tsx`; run `pnpm test`
