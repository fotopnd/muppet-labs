# Architect Output — language-bias-probes

**Role:** architect  
**Sequence:** new-project-full  
**Date:** 2026-06-13  
**Step:** 3 of 9

---

## System Overview

language-bias-probes extends red-team-platform in-place with four new concerns: (1) a seeder that loads a hand-authored multilingual corpus into new DB tables; (2) a bias attack runner that fires each language variant at Ollama and stores responses; (3) a scorer that computes cosine distance between language pairs using a sentence embedding model; (4) a FastAPI endpoint and React route that render results as a government × language divergence heatmap. All four concerns live in a new `red_team_platform/bias/` module. The existing `runner/attack.py` gains `--mode` and `--language` flags that dispatch to the new runner when `--mode bias` is given. Nothing in the existing modules is restructured — only `api/main.py`, `runner/attack.py`, and `pyproject.toml` are modified.

---

## Planner Open Questions — Resolved

| Q | Decision |
|---|----------|
| Q1 — DB schema | Normalised: `bias_probes` + `bias_prompt_variants` + `bias_responses` + `bias_divergence_scores`. Variant-level FK keeps `bias_responses` clean. |
| Q2 — Reuse `runs` table | No. `runs` has a non-nullable FK to `attacks.id`. New table, clean boundary. |
| Q3 — CLI integration | Add `--mode` / `--language` options to the existing Typer command in `runner/attack.py`. Dispatch to `bias.runner.run_bias_session()` when `--mode bias`. |
| Q4 — BiasHeatmap placement | New route `/bias` + NavLink in existing top nav. |
| Q5 — Embedder init | Lazy module-level singleton in `bias/scorer.py`. Consistent with `runner/taxonomy_classifier.py`. |
| Q6 — Corpus JSON schema | Add `probe_question_zh`, `probe_question_ru`, `probe_question_ar` nullable string fields to each entry in `bias-corpus.json`. Seed script skips null. |

---

## Corpus JSON Schema

`bias-corpus.json` entries must have this shape (update all 50 entries before seed can run end-to-end):

```json
{
  "topic_id": "cn_01",
  "government": "China",
  "label": "Xinjiang Vocational Education Training Centers",
  "probe_question_en": "What was the purpose...",
  "probe_question_zh": null,
  "probe_question_ru": null,
  "probe_question_ar": null,
  "divergence_hypothesis": "The ZH model will likely frame..."
}
```

The seed script validates that `topic_id` matches `^[a-z]{2}_\d{2}$` and that `probe_question_en` is non-empty. Other language fields may be null.

---

## Data Models

### `bias/models.py` — SQLAlchemy ORM

Uses `Base` imported from `red_team_platform.models` (same metadata as existing tables).

```python
class BiasProbe(Base):
    __tablename__ = "bias_probes"

    id:                  UUID PK default uuid4
    topic_id:            String(20) NOT NULL
    government:          String(100) NOT NULL
    label:               String(200) NOT NULL
    probe_question_en:   Text NOT NULL
    divergence_hypothesis: Text NOT NULL
    created_at:          DateTime(timezone=True) default now()

    variants: list[BiasPromptVariant]  # relationship

    __table_args__: UniqueIndex("uix_bias_probes_topic_id", "topic_id")


class BiasPromptVariant(Base):
    __tablename__ = "bias_prompt_variants"

    id:          UUID PK default uuid4
    probe_id:    UUID FK(bias_probes.id) NOT NULL
    language:    String(5) NOT NULL   # "en" | "zh" | "ru" | "ar"
    prompt_text: Text NOT NULL
    created_at:  DateTime(timezone=True) default now()

    probe:     BiasProbe                # relationship back_populates
    responses: list[BiasResponse]       # relationship

    __table_args__: UniqueIndex("uix_bias_prompt_variants_probe_language", "probe_id", "language")


class BiasResponse(Base):
    __tablename__ = "bias_responses"

    id:            UUID PK default uuid4
    variant_id:    UUID FK(bias_prompt_variants.id) NOT NULL
    model_name:    String(200) NOT NULL
    response_text: Text NOT NULL
    latency_ms:    Integer NOT NULL
    created_at:    DateTime(timezone=True) default now()

    variant: BiasPromptVariant          # relationship back_populates

    __table_args__: UniqueIndex("uix_bias_responses_variant_model", "variant_id", "model_name")
    # Idempotency: do not re-run the same (variant, model) pair.


class BiasDivergenceScore(Base):
    __tablename__ = "bias_divergence_scores"

    id:               UUID PK default uuid4
    probe_id:         UUID FK(bias_probes.id) NOT NULL
    language:         String(5) NOT NULL        # "zh" | "ru" | "ar" (never "en")
    en_response_id:   UUID FK(bias_responses.id) NOT NULL
    other_response_id: UUID FK(bias_responses.id) NOT NULL
    model_name:       String(200) NOT NULL
    cosine_distance:  Float NOT NULL            # 1 - cosine_similarity, range [0.0, 1.0]
    created_at:       DateTime(timezone=True) default now()

    __table_args__: UniqueIndex("uix_bias_div_scores_probe_lang_model", "probe_id", "language", "model_name")
    # On conflict: update cosine_distance (re-scoring is allowed).
```

### Pydantic schemas — `api/schemas.py` additions

```python
class BiasScoreRow(BaseModel):
    topic_id:   str
    government: str
    label:      str
    zh_score:   float | None
    ru_score:   float | None
    ar_score:   float | None

class BiasScoresOut(BaseModel):
    rows: list[BiasScoreRow]
    scored_model: str | None   # model_name of most recent scoring run, or None
```

---

## Module Interfaces

### `bias/seed.py`

```python
class BiasCorpusEntry(BaseModel):
    topic_id: str
    government: str
    label: str
    probe_question_en: str
    probe_question_zh: str | None
    probe_question_ru: str | None
    probe_question_ar: str | None
    divergence_hypothesis: str

def load_corpus(path: Path) -> list[BiasCorpusEntry]:
    """Reads bias-corpus.json, validates each entry, returns list."""

async def seed_bias_corpus(
    session: AsyncSession,
    entries: list[BiasCorpusEntry],
) -> tuple[int, int, int]:
    """
    Upserts BiasProbe rows, then upserts BiasPromptVariant rows for non-null language fields.
    Returns (probes_upserted, variants_upserted, variants_skipped_null).
    """

def main() -> None:
    """CLI entry point for seed-bias-corpus."""
```

Entry point: `seed-bias-corpus = "red_team_platform.bias.seed:main"`

### `bias/runner.py`

```python
async def run_bias_session(
    session: AsyncSession,
    language: str,
    ollama_base_url: str,
    ollama_model: str,
    ollama_timeout_s: int,
) -> int:
    """
    Queries bias_prompt_variants WHERE language = language.
    For each variant, skips if a BiasResponse already exists for (variant_id, model_name).
    Otherwise fires ollama_client.chat(), writes BiasResponse row.
    Returns count of new responses written.
    """
```

No new CLI entry point. Called from modified `runner/attack.py`.

### `bias/scorer.py`

```python
_embedder: SentenceTransformer | None = None   # module-level singleton

def get_embedder() -> SentenceTransformer:
    """Initialises all-MiniLM-L6-v2 on first call, returns cached instance."""

def compute_cosine_distance(text_a: str, text_b: str) -> float:
    """
    Embeds both strings, returns 1 - cosine_similarity.
    Result is clamped to [0.0, 1.0].
    """

async def score_all(
    session: AsyncSession,
    model_name: str,
) -> list[tuple[str, str, float]]:
    """
    For each BiasProbe:
      - Fetches the EN BiasResponse for model_name.
      - For each non-EN language with a BiasResponse for model_name:
          computes cosine_distance(en_response_text, other_response_text)
          upserts BiasDivergenceScore row.
    Returns list of (topic_id, language, cosine_distance) for logging/report.
    Skips probes where EN response or non-EN response is missing.
    """

def write_report(
    scores: list[tuple[str, str, float]],
    probes_by_topic_id: dict[str, BiasProbe],
    path: Path,
) -> None:
    """
    Writes benchmarks/bias-results.md:
      - Government × language divergence table (rows = gov, cols = ZH/RU/AR)
      - Top-5 highest-divergence (topic_id, label, language, score) pairs
    """

def main() -> None:
    """CLI entry point for score-bias. Accepts --write-report flag."""
```

Entry point: `score-bias = "red_team_platform.bias.scorer:main"`

### `api/routers/bias.py`

```python
router = APIRouter(tags=["bias"])

@router.get("/bias/scores", response_model=BiasScoresOut)
async def get_bias_scores(db: AsyncSession = Depends(get_db)) -> BiasScoresOut:
    """
    SQL:
        SELECT
            bp.topic_id, bp.government, bp.label,
            MAX(CASE WHEN bds.language = 'zh' THEN bds.cosine_distance END) AS zh_score,
            MAX(CASE WHEN bds.language = 'ru' THEN bds.cosine_distance END) AS ru_score,
            MAX(CASE WHEN bds.language = 'ar' THEN bds.cosine_distance END) AS ar_score
        FROM bias_probes bp
        LEFT JOIN bias_divergence_scores bds ON bp.id = bds.probe_id
        GROUP BY bp.topic_id, bp.government, bp.label
        ORDER BY bp.government, bp.topic_id
    Returns scored_model from the most recent BiasDivergenceScore row (or None).
    """
```

### Modified: `runner/attack.py`

Add two new options to the existing `@app.command()`:

```python
mode: Annotated[str, typer.Option("--mode")] = "normal"      # "normal" | "bias"
language: Annotated[str | None, typer.Option("--language")] = None  # "en"|"zh"|"ru"|"ar"
```

In `main()`, after the existing preflight checks, dispatch:
```python
if mode == "bias":
    if language not in ("en", "zh", "ru", "ar"):
        raise typer.BadParameter("--language must be one of: en, zh, ru, ar")
    # call run_bias_session (imported from bias.runner)
elif mode == "normal":
    # existing run_session path unchanged
else:
    raise typer.BadParameter("--mode must be 'normal' or 'bias'")
```

The gemma2:9b preflight check applies to both modes.

### Modified: `api/main.py`

```python
from red_team_platform.api.routers import bias
# ...
app.include_router(bias.router)
```

### Modified: `alembic/env.py`

Add before `target_metadata = Base.metadata`:
```python
import red_team_platform.bias.models  # noqa: F401  # registers bias ORM classes in Base.metadata
```

---

## Alembic Migration — `003_add_bias_tables.py`

```python
revision = "003"
down_revision = "002"

def upgrade() -> None:
    op.execute("""
        CREATE TABLE bias_probes (
            id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            topic_id              VARCHAR(20) NOT NULL,
            government            VARCHAR(100) NOT NULL,
            label                 VARCHAR(200) NOT NULL,
            probe_question_en     TEXT        NOT NULL,
            divergence_hypothesis TEXT        NOT NULL,
            created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE UNIQUE INDEX uix_bias_probes_topic_id ON bias_probes (topic_id);

        CREATE TABLE bias_prompt_variants (
            id          UUID       PRIMARY KEY DEFAULT gen_random_uuid(),
            probe_id    UUID       NOT NULL REFERENCES bias_probes(id),
            language    VARCHAR(5) NOT NULL,
            prompt_text TEXT       NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE UNIQUE INDEX uix_bias_prompt_variants_probe_language
            ON bias_prompt_variants (probe_id, language);

        CREATE TABLE bias_responses (
            id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            variant_id    UUID        NOT NULL REFERENCES bias_prompt_variants(id),
            model_name    VARCHAR(200) NOT NULL,
            response_text TEXT        NOT NULL,
            latency_ms    INTEGER     NOT NULL,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE UNIQUE INDEX uix_bias_responses_variant_model
            ON bias_responses (variant_id, model_name);

        CREATE TABLE bias_divergence_scores (
            id                UUID  PRIMARY KEY DEFAULT gen_random_uuid(),
            probe_id          UUID  NOT NULL REFERENCES bias_probes(id),
            language          VARCHAR(5) NOT NULL,
            en_response_id    UUID  NOT NULL REFERENCES bias_responses(id),
            other_response_id UUID  NOT NULL REFERENCES bias_responses(id),
            model_name        VARCHAR(200) NOT NULL,
            cosine_distance   FLOAT NOT NULL,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE UNIQUE INDEX uix_bias_div_scores_probe_lang_model
            ON bias_divergence_scores (probe_id, language, model_name);
    """)

def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS bias_divergence_scores;
        DROP TABLE IF EXISTS bias_responses;
        DROP TABLE IF EXISTS bias_prompt_variants;
        DROP TABLE IF EXISTS bias_probes;
    """)
```

---

## Frontend Data Contract

### `web/src/api/bias.ts`

```typescript
export type BiasScoreRow = {
  topic_id: string
  government: string
  label: string
  zh_score: number | null
  ru_score: number | null
  ar_score: number | null
}

export type BiasScoresOut = {
  rows: BiasScoreRow[]
  scored_model: string | null
}

export function useBiasScores(): UseQueryResult<BiasScoresOut>
// GET /bias/scores via TanStack Query; refetchInterval: false (data doesn't change until re-scored)
```

### `web/src/components/BiasCell.tsx`

```typescript
type BiasCellProps = { score: number | null }

// Colour scale (cosine distance):
//   null          → bg-border (grey), text "—"
//   0.00–0.14     → bg-accent-subtle, text-accent         (low divergence)
//   0.15–0.34     → bg-amber-100 / text-amber-800         (moderate)
//   0.35+         → bg-red-100 / text-red-700             (high divergence)
// Value displayed as 2 decimal places (e.g. "0.42")
```

### `web/src/pages/BiasHeatmap.tsx`

```typescript
// Layout:
//   - Page heading "Cross-lingual Divergence Heatmap"
//   - Subtitle: scored_model name if available, else "No scores yet — run score-bias"
//   - Table: rows = governments (grouped from rows), cols = ZH / RU / AR
//   - Each row group: government name in first column (rowspan = topic count), then label + 3 BiasCell columns
//   - Empty state: "Run uv run score-bias to populate scores" when rows.length === 0
```

---

## Dependencies

```
bias/models.py        → red_team_platform.models (Base)
bias/seed.py          → bias/models.py, red_team_platform.db
bias/runner.py        → bias/models.py, runner/ollama_client.py, red_team_platform.db
bias/scorer.py        → bias/models.py, red_team_platform.db, sentence_transformers
api/routers/bias.py   → bias/models.py, api/schemas.py, api/deps.py
runner/attack.py      → bias/runner.py  (new import, bias mode only)
api/main.py           → api/routers/bias.py
alembic/env.py        → bias/models.py (side-effect import)
web/src/pages/BiasHeatmap.tsx  → web/src/api/bias.ts, web/src/components/BiasCell.tsx
```

No circular dependencies. Existing modules have no new dependencies on `bias/`.

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Error handling | Raise `ValueError` with context for corpus parse errors. Log + continue on individual Ollama failures in runner (same pattern as existing attack runner). Raise `RuntimeError` if scorer called before responses exist for a probe. |
| Configuration | No new settings fields. Reuses existing `ollama_model`, `ollama_base_url`, `ollama_timeout_s`, `database_url`, `sync_database_url` from `Settings`. |
| Logging | `logging.getLogger(__name__)` in each module. INFO for progress, WARNING for skipped nulls and Ollama failures. |
| Testing | Unit tests for `load_corpus`, `compute_cosine_distance`, null-skipping in seed; integration tests for seed upsert idempotency, runner idempotency, and `/bias/scores` aggregation against a real test DB (NullPool pattern, consistent with existing tests). |

---

## Implementation Notes for Implementer

**1. `bias/models.py` Base import:** Import `Base` from `red_team_platform.models`, not from SQLAlchemy directly. This registers the bias tables in the shared metadata so `init_db()` picks them up in tests.

**2. Seed upsert pattern:** Use `INSERT … ON CONFLICT DO NOTHING` (not `DO UPDATE`) for `bias_probes` and `bias_prompt_variants` — the content is static corpus data, not updated after authoring. For `bias_divergence_scores`, use `ON CONFLICT DO UPDATE SET cosine_distance = EXCLUDED.cosine_distance` so re-scoring overwrites stale values.

**3. Runner idempotency:** Before firing Ollama, execute:
```python
existing = await session.scalar(
    select(BiasResponse).where(
        BiasResponse.variant_id == variant.id,
        BiasResponse.model_name == model_name,
    )
)
if existing:
    continue
```
Log `"Skipping variant %s (already scored)"` at DEBUG level.

**4. Scorer: batch vs per-pair embeddings:** `SentenceTransformer.encode()` accepts a list. For efficiency, batch all texts in one call per probe rather than calling encode() twice per pair. Concretely: collect all (en_text, other_text) pairs for all probes, call `embedder.encode(all_texts)` once, then slice the result. At 50 probes × 3 languages = 150 pairs → 300 texts max, one batch call is trivially fast.

**5. `/bias/scores` SQL:** Write as `text()` (raw SQL) consistent with existing routers (see `coverage.py`). The CASE pivot is not expressible cleanly with SQLAlchemy ORM without significant boilerplate.

**6. `cosine_distance` vs `cosine_similarity`:** Store and display cosine *distance* (1 - similarity). Higher = more divergent = more interesting. The colour scale reads intuitively: dark = bad (high divergence).

**7. React table structure:** The heatmap groups rows by government. Since there are 10 governments × 5 topics = 50 rows, sort by `government` then `topic_id`. Use a `<tbody>` per government, with the government name in a header row spanning all 4 columns (label + ZH + RU + AR). Do not use `rowspan` — it's hard to manage in React and the grouping is clear with a styled sub-header row.

**8. `pyproject.toml` changes:** Add `sentence-transformers>=3.0` to `[project] dependencies`. Add two entry points:
```toml
seed-bias-corpus = "red_team_platform.bias.seed:main"
score-bias       = "red_team_platform.bias.scorer:main"
```

**9. Test DB setup:** The existing `tests/conftest.py` uses NullPool + `Base.metadata.create_all`. Because `bias/models.py` imports Base from `red_team_platform.models`, importing `red_team_platform.bias.models` in `test_bias.py` (or conftest) is sufficient to register the new tables before `create_all` runs.

---

## Handoff

Next role: design-brief (project has a new frontend component — the BiasHeatmap tab).  
The design-brief role reads this output and `roles/planner/output/output.md` to lock down the visual register, interaction model, and done criteria for the heatmap before frontend-architect writes component specs.

Key questions for design-brief to resolve: (1) does the heatmap need any interactivity beyond display (hover tooltips? click-to-expand?); (2) what does the empty state look like before any runs; (3) should the divergence colour scale use existing `@theme` accent tokens or new ad-hoc colours.
