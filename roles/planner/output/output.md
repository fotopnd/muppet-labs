# Planner Output — Red-Team Platform Dashboard Refinement v2

**Role:** planner  
**Sequence:** add-feature  
**Date:** 2026-06-13  
**Reads:** `roles/brief/output/output.md`, `_config/project-state.md`

---

## Open Questions Resolved

**Q1 — Which strategy keys are in the DB?**  
API returns 35 distinct strategy keys. Current `strategyDescriptions.ts` covers 6. All 35 need entries.

**Q2 — `dedup=true`: most-recent or highest-score?**  
Most-recent run per `attack_id`. Rationale: the Compare mode goal is "did this attack succeed at least once?" and most-recent reflects the latest test state. Highest-score could be misleading (cherry-picks a lucky successful run). Use `DISTINCT ON (attack_id) ORDER BY attack_id, created_at DESC`.

**Q3 — Analytics.tsx: import vs inline?**  
Import `StrategyComparison` and `RegressionTracker` as components directly into `Analytics.tsx`. Remove the outer `<div className="p-4">` from both page components — `Analytics.tsx` controls section padding. This avoids code duplication and keeps each section independently testable.

**Q4 — Back-translate: backend cache vs client-side?**  
Client-side `useState` cache per (topicId, lang) is sufficient. Responses are immutable once generated. No backend caching needed. Backend endpoint should NOT store to DB (no migration).

---

## Tech Stack (existing, no changes)

- Backend: FastAPI + SQLAlchemy async + asyncpg, PostgreSQL port 5435, `uv`
- Frontend: React 19, TypeScript strict, Vite, TanStack Query, Recharts, Tailwind v4
- New backend dependency: `anthropic` SDK already available (used by `attack` runner)

---

## File-Level Task List

### Backend changes

| File | Change |
|------|--------|
| `api/routers/runs.py` | Add `dedup: bool = False` query param; when true, use `DISTINCT ON (attack_id)` ORM or raw SQL |
| `api/routers/bias.py` | Add `POST /bias/back-translate` endpoint; call Anthropic haiku |
| `api/schemas.py` | Add `BackTranslateIn`, `BackTranslateOut` schemas; add `dedup` field to existing `RunListOut` if needed |

### Frontend: new files

| File | Purpose |
|------|---------|
| `src/pages/Analytics.tsx` | New Analytics tab: imports StrategyComparison + RegressionTracker |
| `src/components/AnalyticsSummary.tsx` | Computed prose summary for strategy data |
| `src/components/RegressionSummary.tsx` | Computed prose summary for regression data |
| `src/hooks/useBackTranslation.ts` | TanStack mutation for `POST /bias/back-translate`; client-side cache |

### Frontend: modified files

| File | Change |
|------|--------|
| `src/lib/strategyDescriptions.ts` | Expand from 6 → 35 strategy entries |
| `src/App.tsx` | Remove Coverage / Strategy / Regression tabs; add Analytics tab |
| `src/pages/StrategyComparison.tsx` | Remove outer `p-4` div; add `<Cell>` colour thresholds; add `<AnalyticsSummary>` |
| `src/pages/RegressionTracker.tsx` | Remove outer `p-4` div; add `<RegressionSummary>` |
| `src/pages/AttackBrowser.tsx` | Expand detail panel: scrollable pre, char count, example field rendered |
| `src/pages/FailureClusters.tsx` | Bubble chart axes: X = strategy, Y = category; card grid sorted by % |
| `src/pages/SampleReview.tsx` | Compare mode: use `dedup=true`, remove 200-row hack |
| `src/hooks/useRuns.ts` | Add `dedup?: boolean` to query params |
| `src/components/BiasResponseViewer.tsx` | Call `useBackTranslation` on tab switch; show result in 3rd column |

---

## Sequencing

Phase 1 — Backend (no new migrations):
1. `runs.py`: dedup param
2. `bias.py`: back-translate endpoint
3. `schemas.py`: new Pydantic types

Phase 2 — Frontend shared:
4. `strategyDescriptions.ts`: all 35 entries
5. `AnalyticsSummary.tsx`
6. `RegressionSummary.tsx`
7. `useBackTranslation.ts`

Phase 3 — Frontend pages:
8. `App.tsx`: nav restructure
9. `Analytics.tsx`: new combined page
10. `StrategyComparison.tsx`: colour + summary + remove outer padding
11. `RegressionTracker.tsx`: summary + remove outer padding
12. `AttackBrowser.tsx`: detail panel improvements
13. `FailureClusters.tsx`: axes + sort
14. `SampleReview.tsx`: dedup
15. `BiasResponseViewer.tsx`: back-translation column

---

## Strategy Key → Description Assignments

All 35 strategy keys need entries. Grouped by mechanism:

**Persona injection:**
- `AIM` — Always Intelligent & Machiavellian persona (covered)
- `evil_confidant` — "Confidant" persona: asks model to be a trusted friend with no restrictions
- `evil_system_prompt` — System-prompt override redefining model role (covered)
- `dev_mode_v2` — "Developer mode v2": claims to unlock a hidden developer mode with no content filters

**In-context / few-shot manipulation:**
- `few_shot_json` — Few-shot compliance priming via JSON format (covered)
- `multi_shot_5` — 5 fabricated in-context compliance examples before the harmful request
- `multi_shot_25` — 25 fabricated in-context compliance examples (saturation attack)
- `combination_1`, `combination_2`, `combination_3` — Composites of multiple strategies

**Refusal suppression:**
- `refusal_suppression` — Pre-emptive instruction not to refuse (covered)
- `refusal_suppression_inv` — Inverted: ask model to write what a refusal would look like, then invert the output
- `prefix_injection` — Injects "Sure, here is..." prefix to prime the model to continue
- `prefix_injection_hello` — Same with "Hello! Sure, here is..." variant

**Obfuscation / encoding:**
- `base64` — Full prompt encoded in Base64
- `base64_input_only` — Only the harmful substring encoded in Base64
- `base64_output_only` — Ask model to return its answer encoded in Base64
- `base64_raw` — Raw Base64 without standard padding (edge-case variant)
- `rot13` — ROT13 rotation cipher applied to the harmful content
- `leetspeak` — Character substitution: a→4, e→3, i→1, o→0
- `disemvowel` — All vowels removed from the harmful payload
- `obfuscation` — General character-level obfuscation mix
- `low_resource` — Harmful request written in a low-resource language (e.g. Swahili, Yoruba)
- `low_resource_english` — Broken or simplified English intended to evade English-tuned filters

**Output format manipulation:**
- `style_injection_json` — Request output in strict JSON schema to bypass safety filters
- `style_injection_short` — Request an extremely short response to reduce filter surface
- `poems` — Wrap harmful request in a creative poetry framing
- `wikipedia` — Request harmful info in the form of a neutral Wikipedia-style article
- `wikipedia_with_title` — Same with an explicit Wikipedia-style article title provided

**Distractor / noise:**
- `distractors` — Precede or surround the harmful request with irrelevant benign text
- `distractors_negated` — Negated version: explicitly deny harmful intent while embedding the request

**Gradient / automated:**
- `gcg` — Greedy Coordinate Gradient adversarial suffix (covered)
- `autodan` — AutoDAN: automatically generated multi-step jailbreak prompts via discrete optimisation

**Baseline / control:**
- `none` — No jailbreak technique; baseline raw harmful request
- `original_prompt` — The unmodified original attack prompt from the source dataset

---

## Risk Flags

**R1 — `DISTINCT ON` in asyncpg:** `DISTINCT ON` is PostgreSQL-specific syntax. If using `text()` in SQLAlchemy, all params must be non-null (per asyncpg rule from retro). Use ORM or text() with no None params. Recommended: use raw `text()` query since `session_id` will be provided (non-null when dedup=true is used with a session selected), or build with `select(Run).distinct(Run.attack_id)` — verify this maps to `DISTINCT ON` in asyncpg.

Actually: SQLAlchemy's `.distinct()` maps to `SELECT DISTINCT`, not `DISTINCT ON`. `DISTINCT ON` requires raw SQL. Use `text()` with a hardcoded non-null `session_id` — safe since dedup mode requires a session to be selected.

**R2 — Anthropic SDK import in bias.py:** The `anthropic` package must be available in the `red-team-platform` pyproject.toml dependencies. Verify it's already listed (likely is, since the attack runner uses it).

**R3 — Analytics.tsx tab scroll:** Stacking Strategy + Regression in one page creates a long scroll. Add anchor links at the top of the Analytics tab so users can jump to each section.

---

## Handoff

Next role: architect  
Reads this output to design exact API contracts, component interfaces, and data flow. Key decisions to lock:
- Exact SQL for `DISTINCT ON` dedup query
- `POST /bias/back-translate` request/response schema
- `AnalyticsSummary` and `RegressionSummary` prop types
- `useBackTranslation` return type and cache key structure
- Recharts categorical axis design for cluster chart (numeric indices → string labels)
