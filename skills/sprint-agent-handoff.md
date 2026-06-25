# Skill: sprint-agent-handoff

How to distribute sprint units across agents with worktree isolation and merge them safely into main.

---

## Prerequisites

- Sprint manifest is complete (`roles/sprint-planner/output/output.md`)
- All briefs are written (`roles/brief/archive/`)
- Units to run are `pending` and their dependencies are `complete`

---

## Step 1 — Identify which units to launch

From the manifest, select units where:
- Status = `pending`
- `Depends on` is empty OR all listed dependencies are `complete`

Units in the same parallel group (e.g., `01a`, `01b`) can all be launched simultaneously.
Units with a sequential number (`02`) must wait.

---

## Step 2 — Spawn agents with worktree isolation

Use the `Agent` tool with `isolation: "worktree"` for each unit. Worktree isolation gives each agent a clean copy of the repo on a fresh branch — no shared file state between parallel agents.

**Agent prompt template:**

```
You are implementing one unit of a sprint plan for [project name].

Brief: [full path to brief file, e.g. roles/brief/archive/2026-06-22-gridiron-01a-drive-panel-arrows-brief.md]
Project root: [path, e.g. /Users/fotopnd/Documents/muppet-labs/projects/gridiron]
Branch: [branch name from manifest, e.g. sprint/gridiron/01a-drive-panel-arrows]

Instructions:
1. Read the brief file.
2. Run the add-feature sequence starting at planner (brief is already written — skip the brief step).
3. Do not touch any files listed in the brief's Out of Scope section.
4. When implementation and reviewer pass, commit all changes with message: "[slug]: [one-line description]"
5. Do not push or create a PR — commit only.

Files this unit owns: [list from manifest]
```

**Launching parallel units** — send all in one message with multiple Agent tool calls:

```
Agent(description="sprint 01a", isolation="worktree", prompt="...")
Agent(description="sprint 01b", isolation="worktree", prompt="...")
```

---

## Step 3 — Monitor completion

Each agent returns a result when done. Check:
- Did it commit? (agent result will say so, or check `git log` on the worktree branch)
- Did it stay within file ownership? (check `git diff main...<branch> --name-only`)
- Did the reviewer pass?

If an agent returns BLOCKED or FAIL, do not merge. Treat it as a bug-fix candidate (`debug-fix` sequence) before retrying.

---

## Step 4 — Merge each unit

Merge in dependency order. Sequential units must not be merged out of order.

**For each completed unit:**

```bash
# Fetch the branch the worktree agent committed to
git fetch origin sprint/<project>/<id>-<slug>   # if worktree pushed; else it's local

# Fast-forward merge (preferred — keeps history clean)
git merge --ff-only sprint/<project>/<id>-<slug>

# If ff-only fails (diverged), investigate before forcing:
git diff main...sprint/<project>/<id>-<slug> --name-only
# Confirm no overlap with other in-flight branches, then:
git merge sprint/<project>/<id>-<slug>

# Push main
git push origin main
```

**Conflict check before merging any unit:**

```bash
git diff main...sprint/<project>/<id>-<slug> --name-only
```

If this shows a file that's also in another active unit's `Files owned` column → stop. One of them has broken file ownership. Resolve manually before merging either.

---

## Step 5 — Update manifest and unblock

After merging a unit:
1. Update its status in the manifest to `complete`.
2. Check `Depends on` columns — any unit that listed this one is now unblocked.
3. Launch the next wave of agents for newly-unblocked units.

---

## Merge order example

Given manifest:
```
01a (parallel-safe: 01b) → merge either order
01b (parallel-safe: 01a) → merge either order
02  (depends on: 01a, 01b) → do not start until both 01a + 01b are merged
03  (depends on: 02) → do not start until 02 is merged
```

Correct flow:
1. Spawn 01a and 01b in parallel
2. Both complete → merge 01a → merge 01b → push
3. Spawn 02
4. 02 completes → merge 02 → push
5. Spawn 03
6. 03 completes → merge 03 → push

---

## Notes

- `isolation: "worktree"` in the Agent tool creates a temp git worktree automatically. If the agent makes no changes, it's cleaned up. If it does make changes, the worktree path and branch are returned in the result.
- Do not merge two parallel units at the same time without confirming their file ownership is non-overlapping. The manifest's `Files owned` column is the source of truth.
- If a unit's agent modifies a file outside its ownership (bug in the brief), do not merge — revert the agent's work on that file and file a corrective brief.
- **Engine briefs (gitignored files):** Include a `File map` section in the brief listing the key function name, file path, and approximate line number for each file the agent must edit. Gitignored files have no LSP or git blame — without a file map, the agent cold-scans, which wastes tokens and risks editing the wrong location.
