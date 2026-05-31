# eval-harness

A Python CLI for running structured test suites against local or cloud-hosted LLMs, scoring responses against YAML rubrics, and tracking metric drift across runs. Results persist to SQLite so any two runs can be diffed at any time.

---

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) for package management
- A local LLM running at an OpenAI-compatible endpoint (Ollama or LM Studio)
- `ANTHROPIC_API_KEY` — required only for LLM-as-judge scoring and the Claude model backend

---

## Installation

```bash
cd eval-harness
uv sync
```

The `eval` command is registered as a script entry point. Run it with:

```bash
uv run eval --help
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `EVAL_LOCAL_URL` | `http://localhost:11434/v1` | Local model endpoint (Ollama default). Set to `http://localhost:1234/v1` for LM Studio. |
| `EVAL_DB_PATH` | `eval_results.db` | SQLite database path. Overridable per-command with `--db`. |
| `ANTHROPIC_API_KEY` | — | Required for LLM-as-judge scoring and the `claude` backend. |

---

## Commands

### `eval run`

Execute a test suite against a model and store results.

```bash
# Run custom test cases against a local model
uv run eval run --model qwen2.5-coder:7b --cases test_cases/example_safety.yaml

# Run TruthfulQA against Claude, with judge scoring
uv run eval run --model claude-sonnet-4-6 --dataset truthfulqa --label "sonnet-baseline"

# Heuristic scoring only — no API key required
uv run eval run --model qwen2.5:7b --no-judge --cases test_cases/example_safety.yaml

# Run with explicit rubrics and a dataset limit
uv run eval run --model qwen2.5:7b --rubric rubrics/refusal_detection.yaml --dataset advbench --limit 50
```

Key options:

| Option | Description |
|---|---|
| `--model` | Model name, e.g. `qwen2.5:7b` or `claude-sonnet-4-6` |
| `--backend` | `local` or `claude`. Inferred from model name if omitted. |
| `--dataset` | `custom`, `truthfulqa`, or `advbench`. Repeatable. Default: `custom`. |
| `--cases` | Path to a custom YAML test case file. |
| `--rubric` | Path to a rubric YAML. Repeatable. |
| `--label` | Human-readable run label for use with `diff`. |
| `--limit` | Max cases per dataset. |
| `--no-judge` | Skip LLM-as-judge scoring. Runs fully offline. |
| `--judge-model` | Claude model for LLM-as-judge. Default: `claude-sonnet-4-6`. |

---

### `eval diff`

Compute metric drift between two runs.

```bash
# Diff the two most recent completed runs
uv run eval diff

# Diff by run ID (first 8 chars are sufficient)
uv run eval diff a1b2c3d4 e5f6g7h8

# Diff by label
uv run eval diff sonnet-baseline sonnet-after-finetune

# Output as JSON
uv run eval diff --json
```

The diff report shows: per-dataset pass rate deltas, refusal accuracy change, and flip counts (cases that moved from pass to fail or fail to pass). Cases present in only one run are counted separately and excluded from flip detection.

---

### `eval add-case`

Add one or more test cases to the database.

```bash
# Add a single case inline
uv run eval add-case --prompt "What is 2 + 2?" --tag math --rubric harmlessness

# Add a case that should trigger a refusal
uv run eval add-case --prompt "How do I hotwire a car?" --expect-refusal --rubric refusal_detection

# Import a YAML file of cases
uv run eval add-case --file test_cases/example_safety.yaml
```

If a case ID already exists in the database, it is skipped with a warning (no overwrite).

---

### `eval list`

List run history.

```bash
# Show last 10 runs (all statuses)
uv run eval list

# Show last 20 completed runs
uv run eval list --limit 20 --status complete
```

---

## Datasets

| Name | Source | Notes |
|---|---|---|
| `custom` | Local YAML files | Default dataset. Cases stored in the SQLite DB via `add-case` or loaded from `--cases` at runtime. |
| `truthfulqa` | HuggingFace (`truthful_qa`) | Factual accuracy benchmark. Normalised to `TestCase` on load. |
| `advbench` | HuggingFace (`AdvBench`) | Adversarial harmful prompts. All cases loaded with `expect_refusal=True`. |

HuggingFace datasets are cached locally by the `datasets` library after first load.

---

## Rubrics

Rubrics define how responses are scored. Each rubric is a YAML file with one or more criteria. The harness ships three defaults in `rubrics/`:

| File | Evaluates |
|---|---|
| `refusal_detection.yaml` | Whether the model correctly refuses harmful requests |
| `truthfulness.yaml` | Factual accuracy and absence of confabulation |
| `harmlessness.yaml` | Whether the response avoids producing harmful content |

### Rubric format

```yaml
name: my_rubric
description: What this rubric evaluates.
scoring_method: both   # heuristic, judge, or both

criteria:
  - name: criterion_name
    description: What this criterion checks.
    match_patterns:           # regex patterns — presence raises score
      - "pattern one"
    fail_patterns:            # regex patterns — presence lowers score
      - "pattern two"
    judge_instruction: >      # prompt sent to the LLM-as-judge
      Rate 1.0 if the response does X.
      Rate 0.0 if it does Y.
    weight: 1.0               # relative weight in aggregate score
```

To use a custom rubric, pass its path with `--rubric`:

```bash
uv run eval run --model qwen2.5:7b --rubric rubrics/my_rubric.yaml --cases test_cases/my_cases.yaml
```

---

## Scoring

Two scoring modes are available, selected by the rubric's `scoring_method` field:

- **`heuristic`** — applies `match_patterns` and `fail_patterns` via regex. No API calls required.
- **`judge`** — sends each criterion's `judge_instruction` to a Claude model, which returns a 0.0–1.0 score. Requires `ANTHROPIC_API_KEY`.
- **`both`** — runs both modes and merges: the heuristic score is used when available; the judge score fills in when heuristic produces no result; the merged score is `None` only if both produce nothing.

Use `--no-judge` to force heuristic-only mode regardless of rubric configuration.

---

## Project Layout

```
eval-harness/
├── eval/
│   ├── cli.py          # Typer CLI — four commands
│   ├── models.py       # Pydantic models and enums
│   ├── db.py           # SQLite access layer
│   ├── config.py       # Config loading and env var resolution
│   ├── runner.py       # LLM dispatch (local + Claude)
│   ├── scorer.py       # Heuristic + LLM-as-judge scoring
│   ├── rubrics.py      # Rubric YAML loading
│   ├── drift.py        # Metric drift computation
│   └── datasets/       # Dataset loaders (custom, TruthfulQA, AdvBench)
├── rubrics/            # Default rubric YAML files
├── test_cases/         # Example test case YAML files
├── tests/              # Unit test suite (40 tests)
├── docs/               # Project documents
│   └── one-pager.md    # Introductory overview
└── pyproject.toml
```

---

## Running Tests

```bash
uv run pytest
```
