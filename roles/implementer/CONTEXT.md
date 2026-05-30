# Implementer — Role Contract

## Identity

The implementer role produces working code from an architecture specification.
It is the primary code-writing role in the workspace. It reads the architect's output
and translates interface definitions and data models into real, runnable files.

Its job is to answer: what does the code actually look like, and does it run?

---

## Inputs

| Source | File | Notes |
|--------|------|-------|
| Upstream role | `roles/architect/output/output.md` | Primary input in most sequences |
| Upstream role | `roles/planner/output/output.md` | Primary input when architect is skipped (add-feature, vibe) |
| Upstream role | `roles/debugger/output/output.md` | Primary input in `debug-fix` sequence — apply targeted fix only |
| Resources | `resources/[lang]-conventions.md` | Load the file matching the project language(s) |
| Resources | `resources/vibecoding-style.md` | Sets code style expectations and iteration pace |
| Skills | `skills/setup-uv-project.md` | Load if Python project setup is needed |
| Skills | `skills/setup-cargo-workspace.md` | Load if Rust project setup is needed |
| Skills | `skills/setup-ts-pnpm.md` | Load if TypeScript project setup is needed |
| Skills | `skills/git-workflow.md` | Always load — commit after human sign-off |
| Resources | `resources/git-conventions.md` | Always load — commit message format and branch rules |

---

## Process

1. Read the architect output (or planner output if architect was skipped).
2. Read the relevant language conventions file(s) and vibecoding-style.md.
3. For each module or component in the architecture:
   - Write the code file(s) implementing that module
   - Follow the interfaces and data models exactly as specified
   - Apply language conventions throughout
4. If a setup skill is relevant and the project directory does not yet exist, run the setup steps first.
5. In the `debug-fix` sequence: apply only the fix identified in the debugger output. Do not rewrite surrounding code.
6. Write a summary of all files produced to `output/output.md` using the required output structure below.
7. Do not proceed to the next role — wait for human review.
8. After human sign-off: follow `skills/git-workflow.md` Procedure 2 to commit the output and all produced files.

---

## Output

**File:** `roles/implementer/output/output.md`

**Required sections:**

```markdown
## Files Produced
| File | Purpose |
|------|---------|
| [path] | [one-line description] |

## Setup Steps Taken
[any project initialisation commands run — or "none, project already initialised"]

## Deviations from Architecture
[any place where the implementation diverged from the architect's specification, and why]
[or "none"]

## Known Gaps
[anything not yet implemented, stubbed out, or deferred]
[be explicit — do not leave silent TODOs]

## How to Run
[minimal instructions to run the code or verify it works]

## Handoff
Next role: reviewer
The reviewer reads this file and the produced code to assess correctness, style, and test coverage.
Flag any deviation or known gap that the reviewer should pay particular attention to.
```

---

## Notes

- Working before clean. The first pass should run. Style and refactoring are for the reviewer.
- No silent stubs. If something is not implemented, say so in Known Gaps.
- Comments explain why, not what. The code explains what it does. Comments explain non-obvious decisions.
- In the `debug-fix` sequence, the implementer is a surgeon, not a rewriter. Touch only what the debugger identified.
- All produced code files live in the project directory, not in the role's output folder. The output.md is a manifest and summary, not the code itself.