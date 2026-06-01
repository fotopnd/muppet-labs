# CONTEXT.md — Muppet Labs Workspace Routing

## Purpose

This file is the agent's entry point after CLAUDE.md. It describes how to orient to a session,
how roles connect to objectives, and what resources and skills exist. Routing sequences
are defined in `resources/routing.md`.

---

## Role Directory

Each role has a single job. Roles are reusable — the same role can appear in multiple sequences.

**Development roles** — for building software:

| Role | Folder | Job |
|------|--------|-----|
| **brief** | `roles/brief/` | Capture a new project idea. Define success, language, scope, constraints. |
| **planner** | `roles/planner/` | Translate the brief into requirements, tech decisions, and file/module structure. |
| **architect** | `roles/architect/` | Design data models, interfaces, API contracts, and module layout. |
| **implementer** | `roles/implementer/` | Generate working code from the architecture output. |
| **reviewer** | `roles/reviewer/` | Assess output for correctness, style, test coverage, and refactor opportunities. |
| **debugger** | `roles/debugger/` | Diagnose and fix a specific failure. Reads implementer or reviewer output. |
| **retro** | `roles/retro/` | Engineering retrospective after a project or milestone. Feeds improvements back into the workspace. |

**Orientation roles** — outside all sequences, invoke anytime:

| Role | Folder | Job |
|------|--------|-----|
| **daily-brief** | `roles/daily-brief/` | Session-start orientation. Synthesises priorities, project status, and ideas queue into a short actionable brief. |

**Writing roles** — for producing documents about projects:

| Role | Folder | Job |
|------|--------|-----|
| **doc-brief** | `roles/doc-brief/` | Writing intake: lock in audience tier, writing goal, document type, and key messages before any draft begins. |
| **author** | `roles/author/` | Write the document from the doc-brief, the appropriate template, and specified project materials. |
| **doc-reviewer** | `roles/doc-reviewer/` | Formal editor: edit the document in-place for audience fit, goal achievement, and key message coverage. |

---

## Resources Directory

Shared knowledge files in `resources/`. Any role can load any of these. Load only what is relevant.

| File | Contents |
|------|----------|
| `routing.md` | All named routing sequences — ordered role chains for each objective type |
| `python-conventions.md` | Python style, libraries, patterns |
| `rust-conventions.md` | Rust edition, error handling, clippy preferences |
| `typescript-conventions.md` | TS strict mode, module style, tooling |
| `vibecoding-style.md` | Owner's iteration preferences and collaboration style |
| `audience-tiers.md` | Three writing audience tiers: who they are, what they care about, how to calibrate content |
| `doc-types.md` | Catalog of document types: when to use each, which template, which audience tier |
| `writing-voice.md` | Individual writing voice guidance — stub until populated in a voice session |

---

## Templates Directory

Document structure files in `templates/`. Loaded by the `author` role. Each template defines required sections, the purpose of each section, and approximate length. Templates do not specify voice or tone — that is in `writing-voice.md`.

| File | Document Type | Audience | Goal |
|------|--------------|----------|------|
| `technical-deep-dive.md` | Technical Deep-Dive | Technical | Inform / Educate |
| `design-proposal.md` | Design Proposal (RFC) | Technical | Persuade |
| `technical-summary.md` | Technical Summary | Technical Leadership | Inform |
| `executive-summary.md` | Executive Summary | Executive | Inform / Persuade |
| `blog-post.md` | Blog Post / Case Study | General / Public | Educate / Persuade |
| `stakeholder-update.md` | Stakeholder Update | All tiers | Inform |

---

## Skills Directory

Procedural how-to files in `skills/`. Load when a role needs to perform a specific setup
or technical operation. Skills describe steps, not philosophy.

| File | Covers |
|------|--------|
| `setup-uv-project.md` | Initialising a Python project with uv |
| `setup-cargo-workspace.md` | Setting up a Cargo workspace for Rust |
| `setup-ts-pnpm.md` | Initialising a TypeScript project with pnpm |

---

## How Output Flows Between Roles

Each role writes its result to its own `output/output.md`. The next role in the sequence
reads that file as its primary input. The human reviews (and optionally edits) the output
before the next role runs. Edited output is what the next role sees.

```
roles/brief/output/output.md
        ↓
roles/planner/output/output.md
        ↓
roles/architect/output/output.md
        ↓
roles/implementer/output/output.md
        ↓
roles/reviewer/output/output.md
```

The `debugger` role can enter the sequence at any point — it reads from whichever role
produced the failing output.

---

## Routing

All named sequences live in `resources/routing.md`. That file defines:

- The name of the sequence
- The objective it serves
- The ordered list of roles to execute
- Which resources and skills each role should load
- Any conditional branches (e.g. skip architect for small scripts)

**To start a session:** identify the objective, look up the matching sequence in `routing.md`,
confirm the current position in the sequence from `_config/project-state.md`, and execute
the next role.

---

## Role Contract Format

Every role's `CONTEXT.md` follows this structure:

```markdown
# [Role Name] — Role Contract

## Identity
What this role is and what it is responsible for.

## Inputs
- Primary: [path to upstream output.md]
- Resources: [list of resources/ files to load]
- Skills: [list of skills/ files to load, if any]

## Process
Step-by-step description of what this role does.

## Output
- File: output/output.md
- Structure: [H2 sections the output file must contain]
- Handoff: [what the next role does with this output]
```

---

## Session Orientation Checklist

At the start of every session, confirm:

- [ ] Which project is active? (from `_config/project-state.md`)
- [ ] Which objective are we pursuing this session?
- [ ] Which routing sequence applies? (from `resources/routing.md`)
- [ ] Which role is next in that sequence?
- [ ] Are there any blockers logged in `project-state.md` that need resolving first?
