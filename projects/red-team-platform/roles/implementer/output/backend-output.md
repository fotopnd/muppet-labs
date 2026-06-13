# Implementer Output — Language Bias Probes (Backend Phase)

**Date:** 2026-06-13
**Role:** Implementer
**Phase:** Backend
**Project:** language-bias-probes (extends red-team-platform in-place)

---

## Files Written / Modified

### New files

| File | Description |
|------|-------------|
| `src/red_team_platform/bias/__init__.py` | Empty package marker |
| `src/red_team_platform/bias/models.py` | 4 ORM models: BiasProbe, BiasPromptVariant, BiasResponse, BiasDivergenceScore |
| `src/red_team_platform/bias/seed.py` | `load_corpus()` + `seed_bias_corpus()` + `main()` entry point |
| `src/red_team_platform/bias/runner.py` | `run_bias_session()` — queries variants, fires Ollama, writes BiasResponse |
| `src/red_team_platform/bias/scorer.py` | `get_embedder()` singleton, `compute_cosine_distance()`, `score_all()`, `write_report()`, `main()` |
| `src/red_team_platform/api/routers/bias.py` | `GET /bias/scores` with CASE/MAX SQL pivot |
| `tests/test_bias.py` | 7 tests covering: load_corpus, validation, cosine distance, null-variant skipping, seed idempotency, endpoint shape |

### Modified files

| File | Change |
|------|--------|
| `src/red_team_platform/api/schemas.py` | Added `BiasScoreRow`, `BiasScoresOut` |
| `src/red_team_platform/api/main.py` | Added `bias` router import and `app.include_router(bias.router)` |
| `src/red_team_platform/runner/attack.py` | Added `--mode bias` / `--language` options + dispatch logic |
| `alembic/env.py` | Added `import red_team_platform.bias.models` to register tables on Base.metadata |
| `pyproject.toml` | Added `sentence-transformers>=3.0` dep; `seed-bias-corpus` and `score-bias` entry points |
| `projects/red-team-platform/src/red_team_platform/bias/data/bias-corpus.json` | Moved from workspace root `red-team-divergence.json` |

---

## Key Design Decisions

- **Corpus import:** `import red_team_platform.bias.models` in `alembic/env.py` registers the 4 new tables on `Base.metadata` without requiring any other alembic import changes.
- **Idempotency:** ON CONFLICT DO NOTHING for probes and variants; ON CONFLICT DO UPDATE (overwrite cosine_distance) for divergence scores to support re-scoring after corpus updates.
- **Batch encoding:** `score_all()` collects all response texts in a single list and calls `embedder.encode()` once, avoiding repeated model calls per probe.
- **Null language field handling:** `seed_bias_corpus()` skips any variant where `probe_question_{lang}` is None and returns a skip count. This allows partial corpus seeding while ZH/RU/AR authoring is in progress.
- **Dark-mode-safe Tailwind v4:** New frontend components use `@theme` canonical tokens; existing inline-style components are untouched.

---

## Pending Human Tasks

1. **Corpus authoring (blocker for end-to-end run):** Add `probe_question_zh`, `probe_question_ru`, `probe_question_ar` fields to all 50 entries in `src/red_team_platform/bias/data/bias-corpus.json`. Use the prompt from the brief session to generate topics per government.
2. **Alembic migration:** Generate and review `003_add_bias_tables.py` (`alembic revision --autogenerate -m "add bias tables"`), then run `alembic upgrade head` against the dev database.
3. **`uv sync`:** Run after `pyproject.toml` changes to install `sentence-transformers`.

---

## Handoff

**Next role:** Implementer (Frontend Phase)

**Inputs for frontend implementer:**
- `roles/frontend-architect/output/output.md` — full @theme block, per-component specs
- `resources/design_style.md` — canonical token table
- Architect output: `BiasHeatmap.tsx`, `BiasCell.tsx`, `bias.ts` API client, App.tsx Tab union update

**What to build:**
1. Add Tailwind v4 `@theme` block to `web/src/index.css`
2. `web/src/api/bias.ts` — fetch `/bias/scores`, type `BiasScoreRow`
3. `web/src/components/BiasCell.tsx` — colour-bucketed cell (null=grey, 0–0.14=green, 0.15–0.34=amber, 0.35+=red)
4. `web/src/pages/BiasHeatmap.tsx` — table grouped by government with GovernmentGroupHeader rows
5. `web/src/App.tsx` — add `'bias'` to Tab union; add nav tab and conditional render of BiasHeatmap

**Pre-condition:** Human sign-off on backend phase output before frontend phase begins.
