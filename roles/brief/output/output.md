# Brief — Model Behaviour Evaluation Harness

**Sequence:** `new-project-full` | **Role:** brief | **Step:** 1 of 5  
**Date:** 2026-05-31

---

## Project Name

Model Behaviour Evaluation Harness

---

## Description

A Python CLI tool that runs a configurable suite of test prompts against a local Qwen model (via Ollama or LM Studio) or the Claude API, scores responses against defined rubrics using heuristic and LLM-as-judge methods, stores all results in a SQLite database, and tracks metric drift across runs. Includes commands to add custom test cases, run evaluations, diff results between runs, and list run history.

---

## Language(s)

Python

---

## Success Criteria

1. `eval run` executes end-to-end against a local model and stores results in SQLite without errors
2. `eval diff` computes and displays metric deltas between any two completed runs
3. TruthfulQA (HuggingFace) loads and normalises to the internal `TestCase` format
4. AdvBench (HuggingFace) loads and normalises to the internal `TestCase` format with `expect_refusal=True`
5. LLM-as-judge scoring fires against each rubric criterion when `ANTHROPIC_API_KEY` is set
6. Heuristic-only mode (`--no-judge`) runs without any API key or network access beyond the local LLM
7. All unit tests pass: scorer branches, DB roundtrip, drift computation, dataset normalisation

---

## Constraints

- Python only; no polyglot additions
- `uv` for package management; `ruff` for formatting and linting
- No async — synchronous clients throughout (keeps implementation simple, no event loop complexity)
- Storage is SQLite only — no external database, no cloud dependency
- Local LLM accessed via OpenAI-compatible HTTP endpoint (`openai` Python client); works with both Ollama and LM Studio without code changes
- `ANTHROPIC_API_KEY` is required only for: (a) the LLM-as-judge scorer, (b) the Claude model backend
- Responses are scored synchronously after each prompt — no batch scoring

---

## Out of Scope

- Web UI or dashboard
- Concurrent/parallel case execution
- Model fine-tuning or training
- Authentication or multi-user support
- Streaming responses
- Automatic alerting or CI integration (evaluation is a manual run)
- Custom scoring plugins or a plugin architecture

---

## Assumptions

- Local model is already running and reachable before `eval run` is called — the harness does not start or manage the model process
- Default local endpoint: `http://localhost:11434/v1` (Ollama); overridable via `EVAL_LOCAL_URL` environment variable (set to `http://localhost:1234/v1` for LM Studio)
- TruthfulQA and AdvBench are available on HuggingFace under their standard dataset IDs; the `datasets` library handles caching
- Rubrics are authored by the operator in YAML files; the harness ships three default rubrics (`refusal_detection`, `truthfulness`, `harmlessness`)
- Temperature defaults to `0.0` for deterministic, reproducible eval runs
- Dataset column names are stable; if HuggingFace schema changes, loaders will need updating

---

## Handoff

**What this output contains:** Signed-off project brief defining scope, success criteria, constraints, and assumptions.

**Next role:** planner

**What the planner does:** Reads this file and `resources/vibecoding-style.md` + `resources/python-conventions.md` + `skills/setup-uv-project.md`. Produces `roles/planner/output/output.md` with: numbered testable requirements, confirmed technology stack table, top-level file/module structure, and open questions for the architect.

**Caveats:** `resources/python-conventions.md` does not currently exist in the workspace — the planner should skip loading it and apply conventions from `vibecoding-style.md` directly (which contains the Python-specific preferences).
