# CLAUDE.md — Muppet Labs Development Workspace

## Identity

Personal software development workspace for vibecoding and project development.
Root: ~/Documents/muppet-labs/
Editor: VSCode
Languages: Python, Rust, TypeScript

---

## Architecture

This workspace uses a **role-based execution model**.

- **Roles** are reusable context workers, each with a specific job. The same role can appear in multiple routing sequences.
- **Resources** are shared markdown knowledge files used across roles.
- **Skills** are reusable technical procedures (how to do specific things).
- **Routing** defines the ordered sequence of roles required to complete an objective.
- **Outputs** are `output.md` files written by each role, picked up by the next role in sequence.

---

## Folder Map

```
muppet-labs/
├── CLAUDE.md                        ← you are here (Layer 0)
├── CONTEXT.md                       ← workspace routing and session protocol (Layer 1)
│
├── roles/                           ← reusable role definitions
│   ├── brief/
│   │   ├── CONTEXT.md               ← role contract: inputs, process, outputs
│   │   └── output/
│   │       └── output.md
│   ├── planner/
│   │   ├── CONTEXT.md
│   │   └── output/
│   │       └── output.md
│   ├── architect/
│   │   ├── CONTEXT.md
│   │   └── output/
│   │       └── output.md
│   ├── implementer/
│   │   ├── CONTEXT.md
│   │   └── output/
│   │       └── output.md
│   ├── reviewer/
│   │   ├── CONTEXT.md
│   │   └── output/
│   │       └── output.md
│   └── debugger/
│       ├── CONTEXT.md
│       └── output/
│           └── output.md
│
├── resources/                       ← shared markdown knowledge (Layer 3)
│   ├── routing.md                   ← all routing sequences live here
│   ├── python-conventions.md
│   ├── rust-conventions.md
│   ├── typescript-conventions.md
│   └── vibecoding-style.md
│
├── skills/                          ← reusable technical how-to procedures
│   ├── setup-uv-project.md
│   ├── setup-cargo-workspace.md
│   └── setup-ts-pnpm.md
│
├── _config/
│   └── project-state.md             ← current truth: decisions, blockers, progress
│
└── projects/                        ← archived completed projects
```

---

## Operating Rules

1. **Read before acting.** Start every session by reading `CLAUDE.md`, `CONTEXT.md`, `_config/project-state.md`, and `resources/routing.md`.
2. **Execute one role at a time.** A role completes when it has written its `output/output.md`. Do not proceed to the next role without human sign-off.
3. **Roles read from upstream outputs.** Each role's `CONTEXT.md` specifies which other roles' `output.md` files it reads as input.
4. **Resources are shared, not owned.** Any role can load any resource file. Load only what is relevant to the current role.
5. **Skills are procedural.** Load a skill file when a role needs to perform a specific technical procedure.
6. **Update `project-state.md`** at the end of each session and after any significant decision.
7. **Every output.md ends with a Handoff section.** This tells the next role (and the human) what to do with the output.

---

## Session Start Protocol

1. Read `CLAUDE.md` (this file)
2. Read `CONTEXT.md`
3. Read `_config/project-state.md`
4. Read `resources/routing.md`
5. Read `resources/vibecoding-style.md`
6. Confirm with the user: which objective are we pursuing, which routing sequence applies, and which role is next?

---

## Language Defaults

| Language   | Formatter | Linter  | Package Manager |
|------------|-----------|---------|-----------------|
| Python     | ruff      | ruff    | uv              |
| Rust       | rustfmt   | clippy  | cargo           |
| TypeScript | prettier  | eslint  | pnpm            |
