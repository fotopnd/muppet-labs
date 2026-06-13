# python-conventions.md — Python Standards for Muppet Labs

> Language-specific conventions for Python projects.
> Load this file in roles that need language guidance: planner (tech stack), implementer (code production), reviewer (style assessment).
> Do not load for roles that only need working-style guidance — use `vibecoding-style.md` for that.

---

## Package Management

- Use `uv` for all package management. No pip, no poetry, no conda.
- Follow `skills/setup-uv-project.md` to initialise a new project correctly.
- Lock file (`uv.lock`) is committed. Dependency versions are pinned via `>=` minimums in `pyproject.toml`.

## Formatting and Linting

- Format and lint with `ruff`. No black, no flake8, no isort separately.
- Standard `ruff.toml`: `line-length = 100`, `select = ["E", "F", "I", "UP", "B"]`.
- Run `ruff check` and `ruff format --check` before considering implementation done.
- The implementer runs both; the reviewer confirms both pass.

## Type Hints

- Type hints on **all** function signatures — parameters and return types.
- Use `from __future__ import annotations` at the top of every file for forward references.
- Use `X | None` not `Optional[X]`. Use `X | Y` not `Union[X, Y]`.
- Use `list[X]`, `dict[K, V]`, `tuple[X, Y]` (lowercase) not `List`, `Dict`, `Tuple` from `typing`.
- Use `from datetime import UTC` and `datetime.now(UTC)` — never `datetime.utcnow()` (deprecated in 3.12).

## Structured Data

- Use Pydantic v2 or dataclasses for structured data. No bare dicts for domain objects.
- Pydantic preferred when: data is loaded from external sources (YAML, JSON, API), validation is needed, or the model is serialised to storage.
- Dataclasses preferred for: internal-only lightweight data transfer objects with no validation.
- Never use `Any` as a field type unless the field genuinely holds arbitrary external data.
- **pydantic-settings with a shared `.env`:** always set `extra="ignore"` on the `model_config`. A shared `.env` (e.g. one used by both API and frontend) will contain keys the model doesn't declare — without `extra="ignore"`, pydantic-settings raises `ValidationError` on startup.

## File and Path Handling

- Use `pathlib.Path` everywhere. Never `os.path`, `os.getcwd()`, or string concatenation for paths.
- Accept `Path` objects in function signatures, not `str`.

## Error Handling

- Raise specific exceptions with context: `raise ValueError(f"Invalid rubric file {path}: {exc}") from exc`.
- Use `from exc` or `from None` on all re-raises inside `except` blocks.
- Do not catch broad `Exception` unless it is at a boundary (CLI top-level, retry loops).
- Do not swallow exceptions silently.
- **At a legitimate boundary** (consumer loop, retry handler, batch processor): always log with `exc_info=True` to preserve the full traceback. `logger.warning("...", exc_info=True)` — never log only the exception message, which drops the location.
- **Methods requiring prior initialisation** (model weights, DB connection, external resource): raise on uninitialised state rather than returning a silent default. Use `raise RuntimeError("...")` — not `if self._pipe is None: return 0`. Silent defaults write wrong data with no trace.

## Imports

- Standard library → third-party → first-party. `ruff` enforces this automatically.
- Defer slow imports (e.g. `import datasets`, `import anthropic`) inside function bodies when they penalise CLI startup time.
- Never import at module level anything that makes network calls or has side effects on import.

## Testing

- Use `pytest`. Test files in `tests/`, named `test_<module>.py`.
- Fixtures in `tests/conftest.py`.
- Prefer real objects over mocks. Use mocks only for: external HTTP calls, API clients, file system operations that would be slow or destructive.
- Use `pytest-httpserver` to mock HTTP endpoints rather than monkeypatching the requests library.
- Test all non-trivial branches. If a branch exists, it should have a test.
- **Aggregation endpoints** (endpoints that compute derived values — accuracy, latency percentiles, totals): include at least one test with seeded data that asserts computed outputs, not just response shape. An empty-DB test verifies structure; it does not verify the SQL.

## Enums

- Use `StrEnum` (Python 3.11+) instead of `(str, Enum)` for string enums. Ruff UP042 enforces this.

## SQLAlchemy

- `create_engine` allocates a connection pool — call it once per process, not per request, message, or loop iteration.
- Store the engine as a class attribute (created in `__init__`) or module-level singleton. Never call `create_engine` inside a Kafka consumer loop, FastAPI route handler, or background worker tick.
- `Session(engine)` as a context manager is correct for sync writes; `AsyncSession` for async routes.
- **asyncpg NULL parameter rule:** Never pass `None` as a parameter to a `text()` query where the SQL pattern is `$1 IS NULL OR col = $1`. asyncpg uses the PostgreSQL extended protocol, which requires type inference upfront — for `$1 IS NULL`, there is no type context, and asyncpg raises `AmbiguousParameterError`. Rule: if any filter parameter can be `None`, build conditional WHERE clauses using ORM `.where()` calls instead. Use `text()` only when all parameters are guaranteed non-null at the call site.

## API Aggregation Endpoints

- Never filter in Python what can be filtered in SQL. Push `WHERE` conditions to the query.
- `total` / `count` fields in API responses must come from a SQL `COUNT(*)` against the full table, not from `len()` on a Python-filtered slice of a `LIMIT`-ed result. A Python count is wrong as soon as there are more rows than the limit.
- **PostgreSQL does not support `avg(boolean)`**. To compute a success rate from a boolean column: use `func.sum(case((col == True, 1), else_=0)).label("successes")` and `func.count().label("total")` (both valid integer aggregates), then divide in Python: `successes / total if total > 0 else 0.0`. Do not use `func.avg(boolean_col)` — it raises a PostgreSQL type error at runtime, not at query-build time.

## HuggingFace Trainer (fine-tuning projects)

- Always add `accelerate` as an **explicit** dependency when `Trainer` is in scope. It is a hard runtime dep of `transformers.Trainer` in versions ≥5.x and is not auto-installed.
- `no_cuda` was removed in transformers 5.x. Use Trainer auto-detection (MPS → CUDA → CPU). Do not pass `no_cuda` to `TrainingArguments`.
- `warmup_ratio` was removed in transformers 5.2. Use `warmup_steps` (integer) instead.
- `eval_strategy` and `save_strategy` must use the same value (e.g. both `"epoch"`) when `load_best_model_at_end=True`. Mismatched values raise a config error at `Trainer.__init__`.
- Deferred imports inside training functions are correct for slow HuggingFace loads. When patching in tests, patch at `transformers.AutoModelForSequenceClassification.from_pretrained` (the source), not at the module-level name — deferred imports create no module-level binding to patch against.
- **Dataset field verification:** Before using dataset field values as code constants (label strings, category names), verify exact values programmatically — do not infer from the model card description, which uses human-readable names that often differ from raw field values. Run `load_dataset(..., split='train[:20]')` and inspect the relevant field. A mismatch silently produces wrong labels with no error at training time.
- **Model ≠ dataset on HuggingFace Hub:** The model at `huggingface.co/{org}/{model}` and the dataset at `huggingface.co/datasets/{org}/{name}` are separately gated resources with different paths. Do not infer the dataset path from the model name — look it up directly (e.g. model: `allenai/wildguard`, dataset: `allenai/wildguardmix`). The dataset also requires a config name: `load_dataset('org/name', 'config-name', split='train')`.

---

## General Style

- **Working before clean.** The first pass should run. Refactoring is the reviewer's job.
- **Explicit over clever.** Readable over terse. Variable names should describe what they hold.
- **No placeholder stubs.** Do not write `# TODO: implement this` without noting it explicitly in the role output file.
- **Comments explain why, not what.** Code explains what. Comments explain non-obvious constraints or workarounds.
