# vibecoding-style.md — How We Work Together

> This file tells the agent how the owner of this workspace prefers to iterate.
> It is Layer 3 reference material: load it at the start of every session.
> It does not change per-project. It reflects the owner's working style.

---

## Iteration Philosophy

This workspace is built for vibecoding: fast, generative, exploratory development.
The goal is working software over perfect software, momentum over completeness.

- **Small increments over large scaffolds.** Produce something runnable before producing something complete.
- **Output first, explanation after.** Write the code or artifact, then briefly explain key decisions if needed. Do not pre-explain before producing.
- **Assume competence.** The owner understands code. Skip obvious comments and beginner-level explanation unless asked.
- **One thing at a time.** Complete the current role's objective cleanly before suggesting what comes next.

---

## Collaboration Style

- **Ask one question, not five.** If something is ambiguous, identify the single most important unknown and ask that. Do not front-load clarifying questions.
- **State assumptions explicitly.** If proceeding without asking, say what you assumed and why in one line.
- **Show your routing.** When starting a session, confirm which role is executing and which sequence it belongs to. This keeps the owner oriented.
- **Flag divergence early.** If the current role's output is likely to conflict with a decision in `project-state.md`, say so before writing output.

---

## Code Preferences

- **Working before clean.** The first pass should run. Refactoring is for the review role.
- **Explicit over clever.** Readable code over terse code. Variable names should be descriptive.
- **No placeholder logic.** Do not write `# TODO: implement this` or stub functions without noting them explicitly in the output file.
- **Comments explain why, not what.** The code explains what. Comments explain non-obvious reasoning.

### Python
- Use `uv` for package management
- Format and lint with `ruff`
- Type hints on all function signatures
- Prefer `pathlib` over `os.path`
- Dataclasses or Pydantic for structured data, not bare dicts

### Rust
- Edition: 2021
- Error handling: `anyhow` for applications, `thiserror` for libraries
- Run `clippy` before considering implementation done
- Prefer `cargo` workspaces for multi-crate projects

### TypeScript
- Strict mode always on
- `pnpm` for package management
- `prettier` + `eslint` for formatting and linting
- Prefer named exports over default exports
- Avoid `any` — use `unknown` and narrow it

---

## Output Style

- **Write outputs as markdown files to the role's `output/output.md`** unless the output is code, in which case use the appropriate file extension.
- **Structure output files with clear sections.** Use H2 headings to separate concerns so the next role (or the human) can navigate quickly.
- **End every output file with a `## Handoff` section** that states: what this output contains, what the next role in the sequence should do with it, and any caveats.

---

## Vibe Mode vs. Structured Mode

**Vibe mode** (default for new ideas and exploratory work):
- Brief intake, skip formality, move fast
- The routing sequence may be shortened — `00_brief` and `01_planning` can collapse
- Output quality is draft-grade; iteration is expected
- Human edits to `output.md` files are part of the process

**Structured mode** (for production work, complex systems, or multi-session projects):
- Full routing sequence, all roles execute in order
- Each role waits for explicit human sign-off before the next runs
- `project-state.md` is updated after every role, not just every session
- Output quality is production-grade before handoff

To switch modes, the owner says "vibe mode" or "structured mode" at the start of a session.
Default is vibe mode unless the owner specifies otherwise.
