# Retro — Model Behaviour Evaluation Harness

**Role:** retro | **Date:** 2026-05-31  
**Inputs:** `roles/reviewer/output/output.md`, `roles/implementer/output/output.md`, `_config/project-state.md`, `resources/routing.md`, `resources/vibecoding-style.md`

---

## Project

**Name:** eval-harness  
**Sequence:** `new-project-full`  
**Sessions:** 1 (single sitting, 2026-05-31)  
**Roles that ran:** brief → planner → architect → implementer → reviewer → retro  
**Debug-fix runs:** 0  
**Blockers encountered:** 0 (formal), 1 environmental (uv not installed; resolved inline)

---

## What Went Well

**1. Pre-designed architecture via plan mode**

The plan mode session substantially designed the architect output before the roles ran. This meant the architect role was a synthesis and validation pass rather than a blank-sheet design exercise. The four open questions (OQ1–OQ4) were each proposed with an answer by the planner and simply confirmed by the architect — no back-and-forth. The result was a clean, confident implementer handoff. Worth preserving: when a project is well-specified at intake, this is efficient. The architect should not feel obligated to re-derive what the plan already settled.

**2. Open questions proposed with answers**

The planner's four open questions all came with a `Proposed answer:` inline. This made the architect's resolution mechanical rather than creative, and kept the role sequence moving without human intervention between planner and architect. This pattern — raise the question + propose the default — should be codified as expected planner behaviour.

**3. Reviewer findings were complete and immediately actionable**

All five reviewer findings (C1, C2, S1, S2, T1) were fixed in a single follow-up pass: 5 code changes + 4 new tests, committed in one shot. The reviewer output was well-structured: severities were clear, files and line numbers were specified, and refactor candidates were distinguished from blockers. Zero ambiguity about what to do.

**4. Role output chain was linear with no re-reads**

Each role read exactly one upstream output. No role needed to go back further than its immediate predecessor. Handoff sections were populated and used. This is the sequence working as designed.

**5. Smoke test on first try**

The end-to-end smoke test (`eval run` against `qwen2.5-coder:7b`) ran cleanly without any debugging. Mean score 1.000, refusal accuracy 1.000, `eval diff` showed correct zero drift between identical runs. This is attributable to: (a) the architect specifying exact interfaces before implementation, (b) the test suite covering the runner against a mock HTTP server so the code path was already validated before touching a live LLM.

---

## What Could Have Gone Better

**1. `skills/setup-uv-project.md` was missing**

The planner referenced this skill but it didn't exist. The setup steps (uv init, uv add, pyproject.toml entry point, build system config) were duplicated inline in the planner output. This meant the planner output was longer than it needed to be, and those steps are not reusable for the next Python project. **This is the clearest gap in the workspace.**

**2. `resources/python-conventions.md` was missing**

The planner and architect both note "apply conventions from vibecoding-style.md directly" as a workaround. `vibecoding-style.md` contains Python preferences (uv, ruff, pathlib, Pydantic, type hints) embedded inside a broader collaboration style document. Extracting these into a dedicated `python-conventions.md` would: (a) make it loadable independently by roles that only need language guidance, (b) allow `vibecoding-style.md` to stay lean.

**3. pyproject.toml structure required a debugging detour**

When `uv add` was run before a build system was configured, it wrote `requires-python` and `dependencies` under `[tool.uv]` instead of `[project]`. This is a uv quirk when the project has no proper `[project]` table. The correct workflow is: write the full `[project]` table first, then run `uv add`. The `setup-uv-project.md` skill would have documented this.

**4. uv was not installed — discovered mid-session**

The first `uv` call failed. Installation happened inline (curl installer). This could have been caught earlier if the workspace had a "known environment state" section in `project-state.md`. It wasn't a significant blocker but added friction.

**5. Architect output was overlong relative to what the implementer consumed**

The architect output contained detailed YAML examples for rubric files. These were re-created from scratch during implementation — the implementer did not copy from the architect's examples. The architect's job is interfaces and decisions, not worked examples of the artefacts the implementer will produce. The YAML examples added length without adding handoff value.

**6. Retro is not in the routing sequence**

`new-project-full` defines 5 steps. The retro role exists but is not listed as step 6. Without it in routing, it relies on the human to remember to call it. For a "complete" project cycle, the retro should appear as an optional final step.

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| Plan mode | Architecture designed in full before planner/architect roles ran; same design replicated across three documents (plan, planner output, architect output) | Medium | Accept this for complex projects. For simpler scopes, use `new-project-vibe` which collapses brief+planner. Add a note to routing.md: "if plan mode was used, architect may read the plan output directly and skip redundant derivation." |
| Architect output | Detailed YAML examples for rubric files — not consumed by implementer as reference, re-created independently | Low | Remove example artefacts from architect output template. Architect specifies schema and constraints; implementer writes the file. |
| Planner output | uv setup steps inline (14 lines) because `skills/setup-uv-project.md` is missing | Low | Create the skill file; planner references it with one line |
| vibecoding-style.md | Loaded by brief, planner, and implementer; contains Python-specific content that is only relevant to language-specific roles | Low | Extract Python content to `python-conventions.md`; roles that don't need language guidance load only `vibecoding-style.md` |
| Reviewer output | Listed all 26 code files in the scope section; only 5 files were actually discussed in findings | Low | Reviewer should read the manifest from implementer output but only list files that generated findings. Remove "files reviewed" section from reviewer output if findings are file-specific. |

### Redundancy Patterns

- The **project description** appeared verbatim in: the user's /plan args, the brief output, the planner output summary, the architect system overview, and the project-state.md. Five copies. Only the brief output and project-state.md entries are load-bearing for future sessions.
- The **open questions + proposed answers** in the planner output were reproduced as "resolved" in the architect output. The architect output need only state the resolution, not re-quote the question.
- The **`vibecoding-style.md` working-before-clean principle** was quoted or paraphrased in the brief, planner, and architect outputs. It is already in a shared resource; roles should rely on it being loaded rather than restating it.

### Scoping Recommendations

1. **Planner** input table: remove `vibecoding-style.md` if `python-conventions.md` exists and is comprehensive. The planner's job is requirements and structure, not style.
2. **Architect** input table: architect does not need `vibecoding-style.md` — it has no bearing on data models or interfaces. Remove it from the architect's load list.
3. **Brief** input table: `vibecoding-style.md` is correct here — it sets vibe vs structured mode. Keep.
4. **Implementer** input table: should load `python-conventions.md` (language-specific) + `vibecoding-style.md` (working style). Correct as-is once the conventions file exists.

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `resources/vibecoding-style.md` | Extract the Python, Rust, and TypeScript subsections into `resources/python-conventions.md`, `resources/rust-conventions.md`, `resources/typescript-conventions.md`. Replace with a single line: "Language conventions are in `[lang]-conventions.md`." | Reduces load for roles that only need style, not language specifics | No |
| `resources/routing.md` | Add step 6 to `new-project-full`: `retro` role, reads reviewer output + project-state, produces `roles/retro/output/output.md`. Mark as optional. | Retro exists but is absent from the sequence | No |
| `resources/routing.md` | Add a note under `new-project-full`: "If plan mode ran before the sequence, the architect may treat the plan file as a pre-resolved planner output and skip re-deriving decisions already settled there." | Reduces redundancy when plan mode is used | No |

### Skills to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `skills/setup-uv-project.md` | **Create this file.** Content: `uv init <name> --python 3.12`, write full `[project]` table first, then `uv add` dependencies, `uv add --dev` for dev deps, add `[project.scripts]` entry point, add `hatchling` build system + `[tool.uv] package = true` for CLI projects, `uv sync`, verify with `uv run <entry>`. Include the pyproject.toml key-ordering gotcha (uv writes deps under `[tool.uv]` if `[project]` is incomplete). | Referenced by planner but missing; caused inline duplication and a pyproject.toml debugging detour | No |

### Routing Changes

| Sequence | Change | Reason | Human decision required? |
|----------|--------|--------|--------------------------|
| `new-project-full` | Add step 6: `retro` (optional) | Retro role exists but is absent from the canonical sequence | No |
| `new-project-vibe` | No change | Retro is overkill for vibe-mode projects | — |

### New Resources or Skills Needed

**`resources/python-conventions.md`** (extract from `vibecoding-style.md`)  
Proposed content: uv for package management, ruff for lint/format, type hints on all signatures, pathlib over os.path, Pydantic v2 or dataclasses for structured data, no bare dicts, working-before-clean for first pass.  
Roles that would load it: planner (tech stack confirmation), implementer (code production), reviewer (style assessment).

**`_config/project-state.md` template addition — `## Known Environment` section**  
Proposed content: a table listing tool versions and installation status (uv, ruff, Ollama, ANTHROPIC_API_KEY, etc.) to be filled in at the start of a project. Prevents mid-session environment discovery.  
Roles that would use it: implementer (setup steps), anyone running CLI tools.

---

## One Change to Make Now

**Create `skills/setup-uv-project.md`.**

This was the most direct cause of planner output bloat (inline setup steps) and the pyproject.toml corruption detour. The skill file is self-contained, reusable across all future Python projects, and would have prevented both issues in this project. 

The file should include, at minimum:
1. `uv init <name> --python 3.12` — note that it creates a `main.py` stub to delete
2. Write the complete `[project]` table in `pyproject.toml` before running `uv add` (avoids the `[tool.uv]` contamination bug)
3. `uv add <deps>` + `uv add --dev <dev-deps>`
4. For CLI entry point projects: add `[project.scripts]`, `[build-system]` (hatchling), `[tool.hatch.build.targets.wheel]`, and `[tool.uv] package = true`
5. `uv sync` to verify
6. `uv run <entry> --help` to confirm the entry point resolves

Apply this before the next Python project starts.

---

## Handoff

This output is for human review. No workspace files have been modified.

**Recommended actions (in priority order):**
1. Create `skills/setup-uv-project.md` (highest value, no decision required)
2. Add retro as optional step 6 to `new-project-full` in `resources/routing.md`
3. Create `resources/python-conventions.md` by extracting from `resources/vibecoding-style.md`
4. Add `## Known Environment` section to `_config/project-state.md` template

Update `_config/project-state.md` to record that the retro ran on 2026-05-31 and which of the above were actioned.
