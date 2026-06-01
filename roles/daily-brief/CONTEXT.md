# daily-brief — Role Contract

## Identity

The daily-brief role is a session-start orientation. It reads the workspace's current state —
priorities, active project status, and the ideas queue — and produces a short, actionable brief
that answers two questions:

1. **What can we do right now to move active projects forward?**
2. **What should we start next from the ideas queue?**

It does not plan, architect, or implement. It orients. Output should be concise enough to read
in under two minutes and specific enough to act on immediately.

---

## Inputs

| Source | File | Purpose |
|--------|------|---------|
| Primary | `resources/priorities.md` | Goals, target roles, application timeline, current constraints |
| Primary | `resources/project-status.md` | Delivered state and next steps for all active projects |
| Primary | `_config/project-state.md` | Active project detail: decisions, blockers, last session summary |
| Reference | `resources/project_ideas.md` | Ideas queue with build order and CV gap coverage |

> Load all four. They are all short reads relative to other roles. Do not load language
> conventions files, skill files, or role outputs unless a specific item in the brief requires it.

---

## Process

1. Read all four input files.
2. For each **active project** in `project-status.md`:
   - State current status in one sentence.
   - Identify the single highest-leverage action available right now.
   - Note any blockers that must be resolved before progress continues.
3. Check `priorities.md` for any time pressure, deadlines, or constraints that affect today's focus.
4. From `project_ideas.md` Recommended Build Order, identify:
   - Which project should be started next (first unstarted item in priority order).
   - What the first concrete action is to kick it off (brief role, or a specific command/decision).
5. Flag anything that requires a human decision before work can begin.
6. Write `output/output.md` using the required structure below.

---

## Output

**File:** `roles/daily-brief/output/output.md`

**Target length:** ~30–50 lines. If it is longer, it is not a brief.

**Required sections:**

```markdown
## Brief — [date]

### Active Projects

**[Project name]** — [one-sentence status]
- Next action: [specific, actionable]
- Blocker: [if any — otherwise omit]

(repeat for each active project)

### Next Up from Ideas Queue

**[Project number + name]** — [why it is next: which CV gap it closes, which role it targets]
- To start: [first concrete step — run the brief role, make a tech decision, pick a dataset]

### Flags

[Any decision the human needs to make before the work above can proceed. If none, omit this section.]
```

---

## Notes

- The daily-brief is intentionally not a full role in the development sequences. It does not gate
  work or require sign-off. It is an optional orientation that can be invoked at any time.
- It should not repeat content verbatim from project-status.md. It should synthesise.
- "Next action" must be specific: a command to run, a role to execute, a decision to make, a file
  to create. "Continue working on X" is not a next action.
- If `priorities.md` indicates a hard deadline is near, the brief should reflect urgency. If
  nothing is urgent, it should not manufacture urgency.
- Update `resources/priorities.md` whenever your goals, constraints, or application timeline
  changes. The brief is only as current as that file.
