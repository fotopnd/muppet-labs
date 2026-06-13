# Retro — red-team-platform dashboard refinement v2

**Role:** retro  
**Sequence:** add-feature  
**Date:** 2026-06-13

---

## Project

`projects/red-team-platform/web/` — second dashboard refinement pass addressing 11 user-identified issues: tab consolidation (7→5), strategy taxonomy expansion (6→35 keys), dedup fix in sample review, categorical bubble chart for failure clusters, back-translation in bias viewer.

---

## What Went Well

**W1 — DISTINCT ON solved the dedup problem cleanly.** The `DISTINCT ON (attack_id) ORDER BY attack_id, created_at DESC` pattern delivered the most-recent run per attack in a single query, replacing a client-side group-by that was broken by the 200-row page ceiling. No schema changes needed.

**W2 — Categorical axis encoding via tickFormatter.** Mapping Recharts numeric domain indices to string labels via `tickFormatter={(i) => order[i] ?? ''}` turned an uninformative cluster_id axis into a meaningful strategy × category view. The pattern is reusable for any categorical scatter/bubble chart.

**W3 — TanStack Query staleTime=Infinity for immutable results.** Back-translation results are computed once per (lang, text) pair and never change. `staleTime: Infinity` eliminates refetches without any explicit cache invalidation logic.

**W4 — Deferred import of `anthropic` inside route handler.** Keeps API startup fast even when the SDK is infrequently used. Pattern follows the python-conventions rule for slow imports.

**W5 — Empty-text hallucination caught by adversarial review.** The empty-text guard (`if not body.text.strip(): return BackTranslateOut(translated="")`) was identified through systematic adversarial testing rather than accidental discovery. The frontend `enabled: !!text` guard meant this was not user-visible, but the backend is now correct by construction.

---

## What Went Wrong / Friction Points

**F1 — Strategy key discovery gap (planning friction).** The brief assumed ~6 strategy keys; the actual corpus had 35. The planner needed to call `GET /attacks/strategies` to discover this. A future brief for a project with a known external schema should include a schema audit step, not leave it as a planning open question.

**F2 — Stale UI copy after dedup implementation.** The "first 200 runs" copy in SampleReview was left from v1 and not caught until the reviewer pass. Implementation didn't update copy that contradicted the new behaviour. Reviewer catch, minor.

**F3 — Context compaction between reviewer and retro.** Implementation was done across a context boundary. Reviewer output and retro were written in the resumed session. No information was lost (summary was accurate), but compaction added overhead. Inherent to long sessions; no workspace action.

---

## Workspace Updates Applied

| Resource | Change | Why |
|---|---|---|
| `resources/typescript-conventions.md` | Added **Recharts categorical axis** pattern under Recharts Patterns section | W2 — captures the ordinal-index + tickFormatter pattern for future categorical scatter/bubble charts |
| `resources/typescript-conventions.md` | Added **`staleTime: Infinity`** guidance under TanStack Query | W3 — explicit policy for immutable computed results (back-translation, embeddings, etc.) |
| `resources/python-conventions.md` | Added **`DISTINCT ON` for latest-per-group dedup** under SQLAlchemy section | W1 — captures the pattern for future dedup needs |

---

## Decision Log Entries

| Decision | Reason |
|---|---|
| Categorical scatter axes: ordinal-index + tickFormatter over direct string domain | Recharts XAxis/YAxis only support numeric or time scales natively; string categorical requires mapping |
| staleTime=Infinity for back-translation results | Translation output is deterministic for a given (lang, text) — no expiry needed |
| DISTINCT ON over client-side dedup | Client-side grouping breaks when paginated; server-side DISTINCT ON is a single-query guarantee |

---

## Open Items Carried Forward

None. All 11 brief items shipped. Reviewer verdict PASS WITH NOTES (3 minor fixes applied during review pass; no functional gaps).

---

## Handoff

Sequence complete. Next step: update `_config/project-state.md`, then git commit all new and modified v2 files.
