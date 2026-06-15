# Design Brief Output — red-team-platform v5

**Role:** design-brief
**Sequence:** add-feature
**Date:** 2026-06-15

## UI Features in Scope

Three UI areas receive changes:
1. **CaseReview** — new page replacing SampleReview functionally
2. **AuditLog** — new page (7th tab, but current is 4 so it will be 6th)
3. **Analytics** — existing page gets "Live Feed" collapsible section appended

## CaseReview Page Layout

```
[Header: "Case Review" | mode toggle: Compare / All runs]
[Triage Summary: 3 inline badges — "X auto-safe" (green) | "Y need review" (amber) | "Z auto-flagged" (red)]
[Explainer: "Auto-triage reduces manual queue ~87% — only 0.15–0.75 score range requires human review"]
[Filter toggles: All | Needs Review (default) | Auto-Safe | Auto-Flagged]
[Session selector dropdown]

--- Compare mode (with session selected) ---
[Table: Attack Text | #Total | #Success | #Safe | Triage Tier]
[Selected row → Run Comparison panel]
  [Left: best run card | Right: worst run card]
  Each card shows: harm category, strategy, latency, outcome badge, score bar
  Below each card: Decision Form
    [Reviewer: analyst-1 (small label)]
    [Three buttons: Approve (green) | Flag (amber) | Escalate (red)]
    [Optional: reason textarea (placeholder "Optional reason...")]
    [Submit button]
    [If decision exists: show badge + "Edit" link to toggle back to form]

--- All runs mode ---
[Table: Attack Text | Category | Strategy | Outcome | Score | Triage | Decision Badge]
[Selected row expands RunCard + Decision Form inline]
[Pagination: Prev | Page N | Next]
```

## Decision Badge States

- No decision: no badge (empty)
- approve: green pill "Approved"
- flag: amber pill "Flagged"
- escalate: red pill "Escalated"

## AuditLog Page Layout

```
[Header: "Audit Log"]
[Filters row: [Decision dropdown: All / approve / flag / escalate] [Reviewer dropdown: All / analyst-1 / ...]]
[Table:]
  Timestamp | Reviewer | Run excerpt (first 60 chars of attack_text) | Decision badge | Reason
[Pagination: Prev | Page N of M | Next]
[Empty state: "No audit log entries yet."]
```

## Analytics — Live Feed Section

Added at the bottom of Analytics, below "Top Failures" section:

```
[Collapsible section header: "Live Feed" + chevron toggle]
When expanded:
  [Provenance: "Replaying 11,688 runs collected June 2026"]
  [Controls row: [Play ▶ / Pause ⏸ button] [Speed: Fast | Normal | Slow toggle] [Counter: 2,341 / 11,688]]
  [Scrolling table (last 50 events, newest on top):]
    Run # | Strategy | Model | Harm Category | Score | Jailbreak badge
    Row colour: jailbreak=true → subtle red tint; false → default
  [Starts collapsed; Play opens the EventSource]
```

## Visual Token Conventions (Tailwind v4)

Consistent with existing pages:
- Decision badges: `text-success`/green for approve, `text-warning`/amber for flag, `text-danger`/red for escalate
- Triage tier badges: same colour mapping (auto_safe=green, review=amber, auto_flag=red)
- Table rows: `hover:bg-surface-muted`, selected: `bg-accent-subtle`
- Decision form buttons: bordered variants — green border for Approve, amber for Flag, red for Escalate; selected = filled
- Live Feed rows with jailbreak: `bg-danger/5` (5% opacity red tint)

## Handoff

Next role: frontend-architect
Frontend-architect confirms component tree, hook signatures, and state management for CaseReview and AuditLog pages.
