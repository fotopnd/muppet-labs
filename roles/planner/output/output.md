# Planner Output — language-bias-probes

**Role:** planner  
**Sequence:** new-project-full  
**Date:** 2026-06-13  
**Step:** 2 of 9

---

## Project

**Name:** language-bias-probes  
**Description:** Extends red-team-platform in-place with a cross-lingual bias probe pipeline — running the same safety-relevant prompts in EN, ZH, RU, and AR against a local Ollama model, scoring semantic divergence between languages using all-MiniLM-L6-v2 cosine similarity, and rendering results in a new BiasHeatmap dashboard tab.

---

## Requirements

1. `uv run seed-bias-corpus` loads the 50-entry corpus from `src/red_team_platform/bias/data/bias-corpus.json` into a new `bias_probes` table, and loads all non-null per-language prompt variants into a `bias_prompt_variants` table (`probe_id`, `language`, `prompt_text`). If a language field is null (ZH/RU/AR not yet authored), the row is skipped with a warning, not an error.
2. `uv run attack --mode bias --language zh` (and `ru`, `ar`, `en`) executes all `bias_prompt_variants` rows for that language against the configured Ollama model, stores one `bias_responses` row per variant execution (`variant_id`, `response_text`, `model_name`, `latency_ms`), and does not re-run variants that already have a response for that model.
3. `uv run score-bias` computes cosine similarity between the EN response and each non-EN response for the same `probe_id`, stores one `bias_divergence_scores` row per `(probe_id, language_pair, run_id)`, and prints a summary table to stdout.
4. `uv run score-bias --write-report` writes `benchmarks/bias-results.md` with a government × language divergence table and the top-5 highest-divergence (probe, language) pairs.
5. `GET /bias/scores` returns a JSON array of `{ topic_id, government, label, zh_score, ru_score, ar_score }` rows, with `null` for any language where scoring has not yet run.
6. A `BiasHeatmap` page at route `/bias` in the existing React dashboard renders a government × language divergence grid using score data from `GET /bias/scores`. Each cell is colour-coded by divergence magnitude (0.0–1.0 cosine distance); cells with no data render as grey.
7. All existing red-team tests continue to pass after the migration and new module are added.
8. New bias scorer has ≥ 5 unit/integration tests covering: loading corpus JSON, cosine similarity computation, null-variant skipping in seed, idempotent re-run (no duplicate responses inserted), and the `/bias/scores` aggregation endpoint with seeded data.
9. `uv run ruff check .` and `ruff format --check` pass with zero errors on all new Python files.

---

## Technology Stack

| Concern | Choice | Reason |
|---------|--------|--------|
| Language (backend) | Python 3.12 | Existing project constraint |
| Language (frontend) | TypeScript | Existing web/ stack |
| Package manager (backend) | uv | Existing project constraint |
| Package manager (frontend) | pnpm | Existing web/ stack |
| Formatter / linter | ruff | Existing project constraint |
| DB migrations | Alembic | Already configured; new migration `003_add_bias_tables` |
| Sentence embeddings | sentence-transformers (all-MiniLM-L6-v2) | Brief requirement; CPU-only; auto-downloads on first use via HuggingFace cache |
| Ollama client | Existing `red_team_platform.runner.ollama_client` | Reuse; no new HTTP client |
| Frontend state | TanStack Query | Already in web/ |
| Testing | pytest + pytest-asyncio | Existing constraint |

**New Python dependency:** `sentence-transformers>=3.0`

---

## File and Module Structure

### New Python module

```
src/red_team_platform/bias/
├── __init__.py
├── models.py          ← SQLAlchemy ORM: BiasProbe, BiasPromptVariant, BiasResponse, BiasDivergenceScore
├── seed.py            ← seed-bias-corpus CLI entry point
├── runner.py          ← attack --mode bias extension (new subcommand on existing attack CLI)
├── scorer.py          ← cosine similarity scoring; --write-report output
└── data/
    └── bias-corpus.json  ← 50-entry corpus JSON (already placed 2026-06-13)
```

### New API router

```
src/red_team_platform/api/routers/
└── bias.py            ← GET /bias/scores
```

### New Alembic migration

```
alembic/versions/
└── 003_add_bias_tables.py
```

### New frontend files

```
web/src/
├── pages/
│   └── BiasHeatmap.tsx     ← /bias route; government × language grid
├── components/
│   └── BiasCell.tsx        ← single heatmap cell with score + colour coding
└── api/
    └── bias.ts             ← useBiasScores hook; GET /bias/scores
```

### Modified files

```
src/red_team_platform/api/main.py   ← register bias router at /bias prefix
web/src/App.tsx                     ← add /bias route + NavLink "Bias Heatmap"
pyproject.toml                      ← add seed-bias-corpus, score-bias entry points; add sentence-transformers dep
benchmarks/bias-results.md          ← created by score-bias --write-report (does not exist yet)
```

### Test files

```
tests/
└── test_bias.py    ← ≥5 unit/integration tests (see requirement 8)
```

---

## Pre-condition: Corpus Authoring

The corpus JSON at `src/red_team_platform/bias/data/bias-corpus.json` currently has 50 entries with `probe_question_en` populated. The `probe_question_zh`, `probe_question_ru`, and `probe_question_ar` fields do not yet exist in the JSON.

**Human task (before seed can run end-to-end):** Add ZH, RU, and AR prompt fields to each entry. Use Claude to generate variants in one batch per language, then spot-check for meaning drift. The seed script handles null fields gracefully (skips with a warning), so a partial corpus is safe — EN-only probes can be run while ZH/RU/AR are still being authored.

The architect should lock the corpus JSON schema (Q6 below) — this determines the exact field names the human needs to add.

---

## Open Questions for Architect

**Q1 — DB schema: single table with language columns vs normalised variant table?**  
Proposed answer: Normalised. `bias_probes` (50 rows, one per topic_id). `bias_prompt_variants` (up to 200 rows, one per probe × language). This keeps `bias_responses` clean: one FK to `variant_id`, not a composite (probe_id + language). Partial corpus state (null variants never inserted) is cleanly handled.

**Q2 — Should `bias_responses` reuse the existing `runs` table?**  
Proposed answer: No. `runs` has a non-nullable FK to `attacks.id`. Bias responses reference `bias_prompt_variants.id`. Nullable FKs for one-or-the-other would pollute existing runs queries. New table is the clean boundary.

**Q3 — How does `attack --mode bias` integrate with the existing Typer CLI?**  
Proposed answer: Add `--mode` option (default `normal`) and `--language` option to the existing `attack` Typer app in `runner/attack.py`. When `--mode bias`, the runner reads from `bias_prompt_variants` filtered by language. Existing attack path unchanged. The `--language` flag is only valid and required in bias mode (Typer callback validates).

**Q4 — BiasHeatmap: new route `/bias` or embedded tab in an existing page?**  
Proposed answer: New route `/bias` with a NavLink. The existing tabs (Attack Browser, Coverage, Strategy Comparison, etc.) are separate React Router routes. A new route is consistent and avoids overloading an existing page's query param space.

**Q5 — Sentence embedding model initialisation: lazy singleton or explicit init step?**  
Proposed answer: Lazy singleton in `scorer.py` — initialise `SentenceTransformer("all-MiniLM-L6-v2")` on first call to `compute_scores()`, cached at module level. Consistent with how `taxonomy_classifier.py` handles its HuggingFace model.

**Q6 — Corpus JSON schema: add language fields inline vs separate variant files?**  
Proposed answer: Add `probe_question_zh`, `probe_question_ru`, `probe_question_ar` fields directly to each entry in `bias-corpus.json`. Nullable strings. Keeps the corpus self-contained in one file. Seed script reads one file, no joins needed at import time.

---

## Handoff

Next role: architect  
The architect reads this file and designs: (1) the four new SQLAlchemy ORM models with columns and indices; (2) the Alembic migration `003_add_bias_tables`; (3) the full `attack --mode bias` CLI flow including idempotency check; (4) the scorer's embedding pipeline, cosine distance computation, and report format; (5) the `/bias/scores` API schema and SQL aggregation; (6) the BiasHeatmap component data contract and cell colour scale. Confirm or override the six proposed answers above. Lock Q6 first — it determines what the human needs to author into the corpus JSON.
