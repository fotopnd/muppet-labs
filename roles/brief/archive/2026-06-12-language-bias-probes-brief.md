# Brief — Language Bias Probes

**Sequence:** `new-project-full` | **Role:** brief | **Step:** 1 of N  
**Date:** 2026-06-12

---

## Project Name

language-bias-probes

---

## Description

A red-teaming extension that probes LLM response consistency across languages by sending the same safety-relevant and politically-charged prompts in English, Chinese, Russian, and Arabic, then scoring cross-lingual semantic divergence to identify where a model gives meaningfully different answers depending on the user's language.

---

## Language(s)

Python (extension to red-team-platform); TypeScript (new dashboard tab in red-team-platform frontend)

---

## Success Criteria

1. `uv run seed-bias-corpus` loads a bias probe corpus (government × topic × language prompt variants) into the existing red-team DB
2. `uv run attack --mode bias --language zh` (and `ru`, `ar`, `en`) executes prompts against the configured Ollama model and stores responses
3. A bias scorer computes cosine similarity between the EN response and each non-EN response for the same (government, topic) pair using a local sentence embedding model (all-MiniLM-L6-v2, CPU)
4. Divergence scores are stored per (prompt_variant_id, language_pair) in the existing DB
5. A `BiasHeatmap` tab in the red-team-platform React dashboard renders a government × language divergence grid
6. Results are written to `benchmarks/bias-results.md`
7. All existing red-team tests continue to pass; new bias scorer has unit tests (≥5)

---

## Constraints

- Extends red-team-platform in-place — no new separate project; new DB columns/tables via Alembic migration
- Sentence embedding model (all-MiniLM-L6-v2, ~80MB) runs on CPU — no GPU required
- Ollama model must support multilingual prompts (gemma2:9b handles EN/ZH/RU/AR adequately)
- Corpus is hand-authored: ~10 governments × ~5 topics × 4 languages = ~200 prompt variants
- No external translation API — prompts are written directly in each target language
- Grounded in: "State Media Control Influences Large Language Models" (Nature, 2026)

---

## Out of Scope

- Automated translation of prompts (all variants written by hand or with LLM assistance at authoring time, not at runtime)
- More than 4 languages in v1
- Sentiment analysis or opinion scoring beyond semantic similarity
- Statistical significance testing (exploratory v1)
- New standalone project repo — this is a red-team-platform extension

---

## Assumptions

- gemma2:9b produces coherent responses in ZH, RU, and AR (adequate for semantic similarity scoring even if not fluent)
- The divergence signal will be non-trivial for at least some (government, topic) pairs — confirmed plausible by the Nature 2026 paper
- all-MiniLM-L6-v2 is multilingual enough for cross-lingual cosine similarity (it is — trained on 50+ languages)

---

## Handoff

Next role: planner  
The planner must decide: DB schema extension (new `bias_probes` and `bias_responses` tables vs reuse of existing `corpus`/`runs`); whether `BiasHeatmap` is a new React page or a tab within an existing page; corpus authoring strategy (write 200 prompts manually vs LLM-assisted generation). Flag the corpus authoring as a human task that must happen before the attack runner can be tested end-to-end.
