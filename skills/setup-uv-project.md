# Skill: Setup a uv Python Project

> Load this file when the planner or implementer role needs to initialise a new Python project.
> Follow these steps in order. Deviating from the key-ordering in step 2 causes a known pyproject.toml bug.

---

## Prerequisites

Ensure `uv` is on the PATH:

```bash
which uv || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

---

## Procedure

### Step 1 — Initialise the project

```bash
cd /path/to/parent/
uv init <project-name> --python 3.12
cd <project-name>
rm main.py          # uv creates a stub; delete it
```

This creates: `pyproject.toml`, `.python-version`, `.venv/`, `README.md`.

---

### Step 2 — Write the full `[project]` table before adding dependencies

**This step must come before `uv add`.** If `uv add` runs while `[project]` is incomplete, uv writes `requires-python` and `dependencies` under `[tool.uv]` instead of `[project]`, silently corrupting the structure.

Edit `pyproject.toml` to contain a complete `[project]` table:

```toml
[project]
name = "<project-name>"
version = "0.1.0"
description = "<one-line description>"
readme = "README.md"
requires-python = ">=3.12"
dependencies = []          # placeholder; uv add will populate this
```

If the project exposes a CLI entry point, add this now too:

```toml
[project.scripts]
<command> = "<package>.cli:app"
```

---

### Step 3 — Add a build system (CLI projects only)

CLI entry points require the package to be installable. Add before running `uv add`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["<package-dir>"]   # e.g. ["eval"] or ["src/myapp"]

[tool.uv]
package = true
```

Skip this block for library projects that don't expose a CLI entry point.

---

### Step 4 — Add dependencies

```bash
uv add <dep1> <dep2> ...
uv add --dev pytest ruff
```

After this, `pyproject.toml` will have `dependencies` populated correctly under `[project]`.

---

### Step 5 — Create the package structure

```bash
mkdir -p <package-dir>
touch <package-dir>/__init__.py
mkdir tests
touch tests/__init__.py tests/conftest.py
```

---

### Step 6 — Add `ruff.toml`

```toml
line-length = 100
target-version = "py312"

[lint]
select = ["E", "F", "I", "UP", "B"]
ignore = ["B008"]   # needed when using Typer (function calls in default args)

[lint.isort]
known-first-party = ["<package-dir>"]
```

---

### Step 7 — Add `.gitignore`

```
__pycache__/
*.pyc
*.pyo
.venv/
*.db
.python-version
dist/
*.egg-info/
.pytest_cache/
.ruff_cache/
```

---

### Step 8 — Sync and verify

```bash
uv sync
uv run pytest --collect-only   # should find 0 tests and exit 0
uv run ruff check .            # should exit 0 (no files to lint yet)
```

For CLI projects, verify the entry point resolves:

```bash
uv run <command> --help
```

---

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Running `uv add` before writing `[project]` | `requires-python` appears under `[tool.uv]` | Move `requires-python` and `dependencies` to `[project]` manually |
| Missing `[tool.uv] package = true` | `uv run <command>` fails with "No such file" | Add `[build-system]`, `[tool.hatch...]`, and `[tool.uv] package = true` |
| Forgetting to delete `main.py` stub | Untracked file appears in git status | `rm main.py` |
| `uv` not on PATH | `command not found: uv` | `export PATH="$HOME/.local/bin:$PATH"` |
