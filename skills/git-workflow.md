# git-workflow.md — Git Workflow Skill

> This is a procedural skill file. Load it when a role needs to perform git operations.
> Roles that load this skill: implementer, debugger.
> Read git-conventions.md (resources/) before executing any steps here.

---

## When This Skill Is Used

Load this skill at two points in a session:

1. **Start of a new project** — to initialise the repo and create the project branch.
2. **After human sign-off on a role** — to commit that role's output before the next role runs.

---

## Procedure 1: Initialise a New Project

Run once, at the start of the `brief` or `planner` role on a new project.

```bash
# 1. Navigate to the workspace root
cd ~/Documents/muppet-labs

# 2. Initialise git if not already initialised
git init

# 3. Create .gitignore if it does not exist
# (copy defaults from git-conventions.md)

# 4. Stage and commit the initial workspace structure
git add CLAUDE.md CONTEXT.md resources/ skills/ roles/
git commit -m "init: muppet-labs workspace structure"

# 5. Create and switch to the project branch
# [project-name] comes from the brief output — use the project name slug
git checkout -b project/[project-name]
```

---

## Procedure 2: Commit After Role Sign-Off

Run after the human approves a role's output and before the next role begins.

```bash
# 1. Stage the role's output file
git add roles/[role]/output/output.md

# 2. Stage any additional files the role produced
# For implementer/debugger: stage all code files listed in the output manifest
git add [file1] [file2] ...

# 3. Commit using the convention from git-conventions.md
# Format: [role/sequence]: short description
git commit -m "[role]/[sequence]: [short description]"
```

**Constructing the commit message:**
- `[role]` — the role that just completed (brief, planner, architect, implementer, reviewer, debugger)
- `[sequence]` — the active sequence from `_config/project-state.md`
- `[short description]` — one-line summary drawn from the output.md Summary or Handoff section

**Example:**
```bash
git add roles/implementer/output/output.md src/main.py src/config.py
git commit -m "implementer/new-project-full: add CLI entry point and config loader"
```

---

## Procedure 3: Commit Human Edits to a Role Output

If the human edits a role's output.md before the next role runs, commit the edited version first.

```bash
git add roles/[role]/output/output.md
git commit -m "[role]/[sequence]: human edit — [brief description of what changed]"
```

This preserves the distinction between agent output and human correction in the git history.

---

## Procedure 4: Merge Project Branch to Main

Run when a project is complete or at a named milestone.

```bash
# 1. Ensure all role commits are in place on the project branch
git status  # should be clean

# 2. Switch to main
git checkout main

# 3. Merge with --no-ff to preserve branch history
git merge --no-ff project/[project-name] -m "merge: [project-name] [milestone]"

# 4. Tag the milestone (optional)
git tag v-[project-name]-[milestone]

# 5. Return to the project branch if work continues
git checkout project/[project-name]
```

---

## Quick Reference

| Situation | Procedure |
|-----------|-----------|
| New project, no git yet | Procedure 1 |
| Role completed, human signed off | Procedure 2 |
| Human edited an output.md | Procedure 3 |
| Project done or milestone reached | Procedure 4 |

---

## Checks Before Any Commit

```bash
git status    # confirm only intended files are staged
git diff --staged   # review what is actually being committed
```

Never commit without running `git status` first. Stray files in the working directory are common during active development.
