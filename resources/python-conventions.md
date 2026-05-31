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

## File and Path Handling

- Use `pathlib.Path` everywhere. Never `os.path`, `os.getcwd()`, or string concatenation for paths.
- Accept `Path` objects in function signatures, not `str`.

## Error Handling

- Raise specific exceptions with context: `raise ValueError(f"Invalid rubric file {path}: {exc}") from exc`.
- Use `from exc` or `from None` on all re-raises inside `except` blocks.
- Do not catch broad `Exception` unless it is at a boundary (CLI top-level, retry loops).
- Do not swallow exceptions silently.

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

## Enums

- Use `StrEnum` (Python 3.11+) instead of `(str, Enum)` for string enums. Ruff UP042 enforces this.

## General Style

- **Working before clean.** The first pass should run. Refactoring is the reviewer's job.
- **Explicit over clever.** Readable over terse. Variable names should describe what they hold.
- **No placeholder stubs.** Do not write `# TODO: implement this` without noting it explicitly in the role output file.
- **Comments explain why, not what.** Code explains what. Comments explain non-obvious constraints or workarounds.
