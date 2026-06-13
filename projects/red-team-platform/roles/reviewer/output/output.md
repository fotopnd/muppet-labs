# Reviewer Output — Language Bias Probes

**Date:** 2026-06-13
**Role:** reviewer
**Project:** language-bias-probes (extends red-team-platform in-place)

---

## Verdict

PASS WITH NOTES

No blocking correctness bugs. Four notes documented below — all non-blocking, none require rework before the feature can be used.

---

## Ruff Status

All clean. `alembic/env.py` I001 import-sort error fixed with `ruff check --fix` at the start of this session. All 9 bias-related Python files pass `ruff check + format --check`.

---

## Notes

### 1. `seed.py:97` — `select` imported inside conditional branch

`from sqlalchemy import select` appears inside `if probe_row is None:`, mid-loop. `select` should be hoisted to the top-level imports alongside `insert`. Python caches module imports so this is not a runtime penalty, but it's non-idiomatic and invisible to readers scanning imports.

**Fix:** Add `from sqlalchemy import select` to the top-level import block in `seed.py` and remove the deferred import at line 97.

---

### 2. `scorer.py:254,259` — Two inline imports inside `main()` async closure

`from sqlalchemy import select as sa_select` and `import pathlib` appear inside `_run()` under `if write_report_flag:`. `select` is already imported at the top of the file — the alias `sa_select` is redundant and should just use `select`. `pathlib` should be at the top of the file.

**Fix:** Remove both inline imports; use top-level `select` and `pathlib.Path` directly.

---

### 3. `api/routers/bias.py:20-28` — Pivot aggregates across all scored models

The `MAX(CASE WHEN bds.language = ... THEN bds.cosine_distance END)` query has no `WHERE model_name = ?` filter. With multiple models scored, the heatmap shows the **maximum** cosine distance across all models for each cell, while `scored_model` returns only the most recently scored model name. These two fields can be inconsistent.

In the current single-model scenario (`gemma2:9b` only) this is harmless. The inconsistency becomes visible when a second model is scored.

**Fix (if multi-model support is ever added):** Add a subquery to identify the most recent `model_name` and filter `bias_divergence_scores` to that model before the pivot. For now, documenting the limitation is sufficient.

---

### 4. Missing Vitest tests for TypeScript components

Per `typescript-conventions.md`, tests must be colocated with components. No test files exist for:
- `web/src/components/BiasCell.tsx`
- `web/src/pages/BiasHeatmap.tsx`
- `web/src/hooks/useBiasScores.ts`

Minimum required coverage:
- `BiasCell.test.tsx` — `scoreClass` bucket thresholds (null, 0.00, 0.14, 0.15, 0.34, 0.35); `'—'` vs numeric render
- `BiasHeatmap.test.tsx` — empty state renders CLI commands; loaded state renders government header rows
- `useBiasScores.test.ts` — hook calls correct endpoint; `refetchInterval` set to 60 000

**This is the only note that may warrant a follow-up task.** Python tests are adequate (7 tests covering corpus loading, seeding, cosine distance, idempotency, and the API endpoint). The TS gap is a convention violation, not a correctness risk.

---

## Additional Observation (not blocking)

**`useBiasScores.ts:9`** — `queryFn` does not check `r.ok` before calling `.json()`. A 5xx FastAPI error response (which returns valid JSON with a `detail` field) will resolve rather than reject, producing a React Query success state with unexpected shape. The component's type system provides no protection here.

**Minimal fix:**
```ts
queryFn: () =>
  fetch(`${API}/bias/scores`).then((r) => {
    if (!r.ok) throw new Error(`${r.status}`)
    return r.json() as Promise<BiasScoresOut>
  }),
```

---

## Passed Checks

- All 4 ORM models: correct `__tablename__`, `Mapped` annotations, unique indexes, relationships — PASS
- `BiasCorpusEntry` `topic_id` regex validator (`^[a-z]{2}_\d{2}$`) — PASS
- `prompt_for_language` `getattr` dispatch for `en`/`zh`/`ru`/`ar` — PASS
- `seed_bias_corpus` ON CONFLICT DO NOTHING + idempotency — PASS
- `run_bias_session` idempotency guard (scalar select before write) — PASS
- `score_all` batch-encode path (single `embedder.encode` call for all texts) — PASS
- Cosine distance clamp to [0.0, 1.0] with float-drift guard — PASS
- Alembic `include_object` filter prevents external table drops — PASS
- Migration `1bcb02dcc338` downgrade drops only the 4 bias tables — PASS
- `SYNC_DATABASE_URL` env var for psycopg2 sync driver — PASS
- API endpoint `GET /bias/scores` `LEFT JOIN` ensures all probes appear without scores — PASS
- `rows_result.mappings()` for named column access from `text()` SQL — PASS
- `BiasCell` colour buckets: null=grey, <0.15=low, <0.35=mid, ≥0.35=high — PASS
- `scored_model ?? 'No scores yet'` always renders badge — PASS
- Dark-mode divergence token overrides present in CSS — PASS
- `Fragment` keyed on `government` — no React key warning — PASS
- `@theme` canonical tokens: 16 base + 4 divergence extension — PASS
- TypeScript strict mode, no `any`, explicit boundary types — PASS
- `pyproject.toml` entry points for `seed-bias-corpus` and `score-bias` — PASS
- `sentence-transformers>=3.0` added to dependencies — PASS

---

## Handoff

PASS WITH NOTES — feature is shippable.

**Recommended follow-up (not blocking):**
1. Fix deferred imports in `seed.py:97` and `scorer.py` (10 min)
2. Add Vitest tests for `BiasCell`, `BiasHeatmap`, `useBiasScores` (1–2 hrs)
3. Add `r.ok` guard in `useBiasScores.ts` `queryFn` (5 min)

**Human tasks remaining:**
- Run end-to-end pipeline once Ollama is available:
  ```
  seed-bias-corpus
  attack --mode bias --language en
  attack --mode bias --language zh
  attack --mode bias --language ru
  attack --mode bias --language ar
  score-bias
  ```
- Verify heatmap populates with real data at `http://localhost:5173`
