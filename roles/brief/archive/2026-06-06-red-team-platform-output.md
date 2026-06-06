# Brief Output — red-team-platform

**Role:** brief
**Sequence:** `new-project-full` (step 1)
**Date:** 2026-06-06

---

## Project Name

`red-team-platform`

---

## Description

A local offensive safety evaluation platform that fires public adversarial attack corpora (JailbreakBench + AdvBench) at a local Ollama LLM, scores responses with a DistilBERT pair-classifier checkpoint shared from the llm-safety-monitor project, and surfaces coverage and regression data across a 5-tab React dashboard — serving as the portfolio's offensive complement to the defensive classifier projects.

---

## Language(s)

- **Backend:** Python (FastAPI, SQLAlchemy, uv, ruff, pytest)
- **Frontend:** TypeScript (React, TanStack Query, recharts, shadcn/ui, Vite, pnpm, vitest)
- **Database:** PostgreSQL 16
- **LLM interface:** Ollama HTTP API (local, zero external calls)

---

## Success Criteria

The project is done when all of the following are true:

1. **Corpus loader** — JailbreakBench and AdvBench datasets load from HuggingFace (offline-capable after first pull) and are seeded into the `attacks` table with `harm_category`, `strategy`, and `source` fields.
2. **Attack runner** — a CLI command fires each attack at a configurable local Ollama model; responses are stored in the `runs` table. The runner can target a specific corpus source, harm category, or strategy subset.
3. **Classifier scoring** — each stored response is scored by the `pair_classifier` DistilBERT checkpoint from `resources/models/llm-safety-monitor/pair_classifier/`; `jailbreak_success = (predicted_label == 1)` is written back to the `runs` row.
4. **Coverage heatmap** — the `coverage_summary` materialised view aggregates success rates by `harm_category × strategy`; the FastAPI endpoint `/coverage` returns this in a format ready for the recharts HeatmapChart component.
5. **Dashboard tabs** — the React app has five functional tabs: Attack Browser (paginated attack table with filters), Coverage Heatmap (recharts HeatmapChart), Strategy Comparison (bar chart: ASR per strategy), Regression Tracker (line chart: ASR over run history), Sample Review (prompt + response + classifier label for a selected run).
6. **Regression tracking** — multiple run sessions are stored separately; the Regression Tracker tab shows attack success rate (ASR) per run session, enabling comparison across Ollama model versions.
7. **Tests** — pytest covers: corpus loader (mocked HuggingFace), attack runner (mocked Ollama), classifier scoring (mocked model inference); vitest covers all five tabs with mocked API responses.
8. **Zero external API calls** — the system never contacts any cloud LLM endpoint; all inference uses local Ollama.

---

## Constraints

- **Local only:** Ollama at `http://localhost:11434/v1`; configurable model via `OLLAMA_MODEL` env var.
- **Postgres port 5435** — ports 5432–5434 are taken by other workspace projects; this project uses 5435.
- **Classifier checkpoint is a shared asset:** loaded from `resources/models/llm-safety-monitor/pair_classifier/` via `PAIR_CLASSIFIER_PATH` env var. The checkpoint must already exist (produced by llm-safety-monitor project); this project does not train it.
- **Public academic datasets only:** JailbreakBench (`JailbreakBench/JailbreakBench` on HuggingFace) and AdvBench (loaded from the `llm-attacks` HuggingFace dataset). Both are released specifically for safety research.
- **No Kafka:** attack generation is batch/scheduled; direct DB writes are sufficient.
- **Hardware:** Apple M4 24GB; Ollama running locally. No GPU inference requirement.

---

## Out of Scope

- **Mutation engine (v1):** paraphrase variants, roleplay wraps, base64/leetspeak obfuscation, few-shot priming wrappers — deferred to v2. v1 uses corpus replay only.
- **Live API testing against production LLMs** (OpenAI, Anthropic, etc.) — local Ollama only.
- **Fine-tuning or modifying the pair_classifier** — this project is a consumer, not a trainer.
- **Automated scheduled attack runs** — the runner is invoked manually or via a one-shot CLI call; no scheduler daemon.
- **User authentication / multi-user support** — single-user local dashboard.
- **Jailbreak dataset curation or annotation** — the platform replays existing public corpora; it does not create new attacks.

---

## Assumptions

1. **pair_classifier checkpoint exists** at the path specified by `PAIR_CLASSIFIER_PATH` before the attack runner is invoked. The platform raises `RuntimeError` at startup if the path is missing — no silent fallback.
2. **JailbreakBench dataset structure:** `JailbreakBench/JailbreakBench` on HuggingFace exposes `Goal`, `Category`, and `jailbreaks` fields. `Category` maps to `harm_category`. Attack text is extracted from the `jailbreaks[].prompt` field (or `Goal` when the jailbreaks list is empty, for direct attacks).
3. **AdvBench structure:** loaded from the `llm-attacks/advbench` HuggingFace dataset; `goal` column used as attack text; `harm_category` defaults to `"general_harm"` for AdvBench items that lack category metadata.
4. **Strategy taxonomy:** JailbreakBench items include a strategy tag (e.g. `GCG`, `AutoDAN`, `PAIR`, `direct`). AdvBench items default to strategy `"direct"` since they are base prompts without jailbreak wrapping.
5. **Ollama response format:** standard Ollama `/api/chat` endpoint with `{"model": ..., "messages": [...], "stream": false}`.
6. **"Jailbreak success"** is defined solely by `pair_classifier` output: `predicted_label == 1` (unsafe). No secondary human annotation in v1.
7. **No Kafka** — direct PostgreSQL writes for all attack results. Confirmed for v1.
8. **Tech stack matches workspace conventions** — Python with uv/ruff/pytest; TypeScript with pnpm/vitest/prettier/eslint.

---

## Handoff

**Next role:** planner

The planner reads this file to define requirements, confirm the technology stack, map the top-level file structure, and list open questions for the architect.

**Flags for planner:**
- Assumption 2 and 3 (dataset field names) — HuggingFace dataset schemas can vary; the planner should note that the corpus loader must be inspectable and field names should be defined as constants, not scattered strings.
- Assumption 4 (strategy taxonomy) — confirm the strategy field name in JailbreakBench and define what to do if a JailbreakBench item lacks a strategy tag (recommend: default to `"unknown"`, log a warning).
- Confirm Postgres schema handles multi-session run tracking (separate `run_sessions` records) for the Regression Tracker tab.
- Confirm the `coverage_summary` materialised view refresh strategy: refresh after each run session completes, not per-row.
