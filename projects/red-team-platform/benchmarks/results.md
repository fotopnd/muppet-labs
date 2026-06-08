# Red-Team Platform Benchmark Results

This file is populated after real attack sessions using `uv run attack`.

## Phase 2 sweep configuration

| Parameter | Value |
|-----------|-------|
| Model | gemma2:9b (via Ollama) |
| Classifier package | llm-safety-classifier (shared, editable install) |
| Classifier input | `attack_text [SEP] response_text` (canonical concatenation) |
| Strategies | 6 (gcg, prefix-injection, role-play, persona, few-shot, encoded) |
| Goals per strategy | 300 |
| Total attacks | 1,800 |

## Sessions

| Date | Session ID | Model | Classifier version | Total attacks | Successes | ASR |
|------|-----------|-------|--------------------|---------------|-----------|-----|
| — | — | — | — | — | — | — |

## Notes

- Seed corpus: `sevdeawesome/jailbreak_success` (35 strategies × 300 harm goals)
- Classifier: `pair-2026-06-07` RoBERTa-base checkpoint
- Preflight check: `attack` script rejects runs with `ollama_model != "gemma2:9b"`
- Results are injected into llm-safety-monitor via outbox publisher (`source_dataset=red_team`)
- Run `uv run attack --help` for session options
