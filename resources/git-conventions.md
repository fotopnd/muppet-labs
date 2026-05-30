# git-conventions.md — Muppet Labs Git Conventions

> Shared conventions for all git operations across the workspace.
> Loaded by any role or skill that interacts with git.

---

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable, reviewed work only. Merges from project branches at milestones. |
| `project/[project-name]` | One branch per project. Created at the start of the `brief` role. |

**Branch naming:** use the project name slug from the brief output. Lowercase, hyphens, no spaces.
```
project/muppet-cli
project/rust-api
project/ts-dashboard
```

Never work directly on `main` during active development. Main receives merges, not direct commits.

---

## Commit Message Format

```
[role/sequence]: short description

Optional body: one or two sentences if the change needs context.
```

**Examples:**
```
brief/new-project-full: capture initial project brief for muppet-cli
planner/new-project-full: define requirements and file structure
architect/new-project-full: define data models and module interfaces
implementer/new-project-full: add CLI entry point and config loader
reviewer/new-project-full: pass with notes — flag missing edge case tests
debugger/debug-fix: diagnose null config path on missing env var
implementer/debug-fix: fix null config path handling
```

**Rules:**
- Role and sequence always in the prefix
- Description is lowercase, present tense, under 60 characters
- No full stops at the end of the subject line
- Body only when the change is non-obvious

---

## When to Commit

| Trigger | Action |
|---------|--------|
| Human signs off on a role's output | Commit that role's output and any files it produced |
| Human edits a role's output.md before next role runs | Commit the edited version before proceeding |
| Project branch ready to merge | Merge to main with `--no-ff` to preserve branch history |

**Never commit:**
- Mid-role, before output.md is written
- Before the human has reviewed and signed off
- Partial or broken code unless explicitly noted as a work-in-progress commit

---

## .gitignore Defaults

Add to `.gitignore` at the workspace root:

```
# OS
.DS_Store
Thumbs.db

# Editor
.vscode/settings.json
*.swp

# Language build artifacts
__pycache__/
*.pyc
target/
node_modules/
.pnpm-store/

# Environment
.env
.env.local
```

---

## Tagging

Tag stable project milestones on main after merge:

```
v[project-name]-[milestone]
e.g. v-muppet-cli-mvp
     v-rust-api-v1
```

Tags are optional for vibe projects. Use them when you want a named restore point.

---

## Merging to Main

When a project branch is complete or at a stable milestone:

```bash
git checkout main
git merge --no-ff project/[project-name] -m "merge: [project-name] [milestone description]"
git tag v-[project-name]-[milestone]
```

`--no-ff` preserves the branch history as a distinct unit in the git log. Without it, the role-by-role commit history collapses into main and loses its structure.
