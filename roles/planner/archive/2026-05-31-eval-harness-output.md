# Planner — Model Behaviour Evaluation Harness

**Sequence:** `new-project-full` | **Role:** planner | **Step:** 2 of 5  
**Date:** 2026-05-31  
**Reads:** `roles/brief/output/output.md`, `resources/vibecoding-style.md`  
**Assumption:** `resources/python-conventions.md` does not exist; Python conventions applied from `vibecoding-style.md` directly. `skills/setup-uv-project.md` does not exist; uv steps documented inline.

---

## Project

**Name:** eval-harness  
**CLI entry point:** `eval`  
**Location:** `projects/eval-harness/` (relative to workspace root)  
**Project branch:** `project/eval-harness`

---

## Requirements

Numbered, testable. Each requirement maps to at least one verification step.

| # | Requirement |
|---|-------------|
| R1 | `eval run` accepts `--model`, `--backend`, `--cases` (YAML file), `--dataset` (truthfulqa / advbench / custom), `--rubric` (YAML file), `--label`, `--limit`, `--no-judge`, and `--db` flags and runs successfully against a live local LLM endpoint |
| R2 | Each test case response is stored as an `EvalResult` row in SQLite, including raw response text, latency in milliseconds, and per-criterion scores |
| R3 | Each eval run is stored as an `EvalRun` row with a config snapshot (JSON), start/finish timestamps, total case count, mean aggregate score, and refusal accuracy rate |
| R4 | The heuristic scorer detects refusals unconditionally on every result using `REFUSAL_PATTERNS` and returns `passed=True/False/None` per rubric criterion based on `match_patterns` and `fail_patterns` |
| R5 | The LLM-as-judge scorer calls Claude API once per rubric criterion per result, returns a numeric score (0.0–1.0), a passed bool, and a one-sentence rationale; retries once on malformed JSON |
| R6 | When `scoring_method=both`, heuristic and LLM judge both run; heuristic wins on `passed` disagreement; `score` is the average of both numeric scores |
| R7 | TruthfulQA validation split loads from HuggingFace and normalises to `TestCase` with `reference_answer` populated from `best_answer`, `dataset=DatasetSource.TRUTHFULQA`, and `rubric_names=['truthfulness']` |
| R8 | AdvBench loads from HuggingFace (`walledai/AdvBench`) and normalises to `TestCase` with `expect_refusal=True`, `dataset=DatasetSource.ADVBENCH`, and `rubric_names=['refusal_detection', 'harmlessness']` |
| R9 | Custom test cases load from a YAML file where each list item maps to `TestCase` fields; invalid cases raise with the case index and field name |
| R10 | `eval diff` computes per-run deltas for: `mean_score`, `refusal_rate`, per-rubric mean score, per-dataset mean score, and emits lists of case IDs that flipped from pass to fail or fail to pass |
| R11 | `eval diff` prints a formatted table to stdout; supports `--json` for raw `DriftReport` output and `--no-color` for plain text |
| R12 | `eval list` prints a table of recent runs with columns: truncated ID, label, backend, model, datasets, total cases, mean score, refusal rate, status, started_at |
| R13 | `eval add-case` persists a single `TestCase` to the `test_cases` DB table; `--file` imports all cases from a YAML file in one call |
| R14 | All `db.py` functions use `CREATE TABLE IF NOT EXISTS`; calling `init_db` on an existing database is safe and idempotent |
| R15 | `uv run pytest tests/ -v` passes with no failures |
| R16 | `uv run ruff check eval/ tests/` and `uv run ruff format --check eval/ tests/` both exit 0 |

---

## Technology Stack

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Package manager | `uv` | Workspace standard |
| Formatter / linter | `ruff` | Workspace standard |
| CLI framework | `typer` | Pydantic-friendly; auto-generates `--help`; cleaner than Click for typed commands |
| Data models | `pydantic` v2 | Workspace standard; `model_validator` for computed fields; `model_dump_json` for SQLite serialisation |
| Local LLM client | `openai` (Python SDK) | OpenAI-compatible API works unchanged with both Ollama and LM Studio |
| Claude API client | `anthropic` (Python SDK) | Official SDK; used for both Claude model backend and LLM-as-judge |
| Dataset loading | `datasets` (HuggingFace) | Standard for TruthfulQA and AdvBench; handles caching automatically |
| Config / rubric files | `pyyaml` | YAML for rubric definitions and custom test case files |
| Terminal output | `rich` | Progress bars during `eval run`; formatted tables for `eval list` and `eval diff` |
| Storage | `sqlite3` (stdlib) | No extra dependency; portable single-file DB; sufficient for eval scale |
| Testing | `pytest` + `pytest-httpserver` | `pytest-httpserver` mocks the local LLM HTTP endpoint for runner tests |
| Python version | 3.12 | Current stable; required for modern `typing` features |

---

## File and Module Structure

Top-level only. Implementer fills in internals.

```
projects/eval-harness/
├── pyproject.toml              # uv project config; [project.scripts] entry point
├── .python-version             # "3.12"
├── ruff.toml                   # line-length=100, select=["E","F","I","UP","B"]
├── README.md
│
├── eval/                       # importable package; all logic lives here
│   ├── __init__.py
│   ├── cli.py                  # Typer app; four commands: run, add-case, diff, list
│   ├── models.py               # All Pydantic models — no logic, no imports of other eval modules
│   ├── db.py                   # sqlite3 access layer: init, insert, query helpers
│   ├── config.py               # RunConfig YAML loader; env var resolution for keys and URLs
│   ├── runner.py               # LLM dispatch: local (openai client) or claude (anthropic client)
│   ├── scorer.py               # HeuristicScorer, LLMJudgeScorer, score_result orchestrator
│   ├── rubrics.py              # Rubric YAML loader and validator
│   ├── drift.py                # Metric delta computation; DriftReport formatter
│   └── datasets/
│       ├── __init__.py         # load_dataset(source, config) dispatcher
│       ├── custom.py           # YAML → list[TestCase]
│       ├── truthfulqa.py       # HuggingFace TruthfulQA → list[TestCase]
│       └── advbench.py         # HuggingFace AdvBench → list[TestCase]
│
├── rubrics/                    # Default rubric YAML files (shipped with the project)
│   ├── refusal_detection.yaml
│   ├── truthfulness.yaml
│   └── harmlessness.yaml
│
├── test_cases/                 # Example custom test case files
│   └── example_safety.yaml
│
└── tests/
    ├── conftest.py             # Fixtures: in-memory DB, mock runner, sample TestCase/Rubric objects
    ├── test_models.py          # Pydantic validation: required fields, computed aggregate_score
    ├── test_scorer.py          # Heuristic branches (pass / fail / inconclusive); LLM judge mocked
    ├── test_db.py              # insert + query roundtrip for all three tables; idempotent init
    ├── test_datasets.py        # Custom YAML loading; TruthfulQA + AdvBench with HF mocked
    ├── test_runner.py          # Local runner against pytest-httpserver mock; error handling
    └── test_drift.py           # Zero delta; positive delta; negative delta; empty intersection
```

---

## uv Setup Steps

(Inline since `skills/setup-uv-project.md` does not yet exist.)

```bash
cd /Users/fotopnd/Documents/muppet-labs/projects/
uv init eval-harness --python 3.12
cd eval-harness
uv add typer pydantic anthropic openai datasets pyyaml rich
uv add --dev pytest pytest-httpserver ruff
```

Add to `pyproject.toml` under `[project.scripts]`:
```toml
[project.scripts]
eval = "eval.cli:app"
```

Rename the auto-generated `src/` layout if uv creates one — this project uses a flat `eval/` package at the project root (not `src/eval/`).

---

## Open Questions for Architect

1. **BOTH-mode score merge:** When `scoring_method=both`, if heuristic returns `score=None` (inconclusive) but the LLM judge returns `score=0.8`, should the aggregate use only the judge score or stay `None`? Proposed answer: use the available score; only return `None` if both sides return `None`.

2. **Drift case intersection:** Cases present in run A but not run B (and vice versa) are excluded from flip detection. Should they appear in the drift report at all, e.g. as "cases not in baseline" or "cases not in current"? Proposed answer: include counts only (not full lists) to keep the report readable.

3. **`eval add-case` with `--file`:** Should importing a YAML file with `--file` overwrite existing cases that share an ID, or skip them and report a conflict? Proposed answer: skip and warn — no silent overwrites.

4. **Refusal accuracy metric:** Confirmed definition: `refusal_rate = (true_positives + true_negatives) / total`, where TP = detected refusal on an expect_refusal case, TN = no refusal on a non-expect_refusal case. This is refusal-classifier accuracy, not raw refusal rate.

---

## Handoff

**What this output contains:** Testable requirements (R1–R16), confirmed technology stack, top-level file/module structure, uv setup steps, and four open questions for the architect to resolve.

**Next role:** architect

**What the architect does:** Reads this file. For each module in the file structure, defines: data models it owns, public interface (typed function signatures), and dependencies. Resolves the four open questions above. Writes `roles/architect/output/output.md`.

**Caveats:** The architect output has already been substantially pre-designed during the planning phase. The architect role should validate those designs against the requirements numbered here (especially R4–R6 for scoring, R10 for drift) and resolve the open questions before writing output.
