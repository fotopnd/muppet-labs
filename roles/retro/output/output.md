# Retro — case-queue

**Sequence:** `new-project-full` (step 6 of 6) + post-sequence feature session  
**Date:** 2026-06-02  
**Reads:** `roles/reviewer/output/output.md`, `roles/implementer/output/output.md`, `_config/project-state.md`, `resources/routing.md`, `resources/vibecoding-style.md`

---

## Project

**Name:** case-queue  
**Sequence used:** `new-project-full`, then one unsequenced feature session (`add-feature` equivalent)  
**Sessions:** 2 (2026-06-01 original build; 2026-06-02 UI enhancements + AI reviewer fix)  
**Roles that ran:** brief → planner → architect → implementer → reviewer → retro (this document)  
**Post-sequence work (session 2):** sort columns, decision/actor filters on audit log, AI reviewer system prompt fix, bad-decision DB cleanup

---

## What Went Well

**Backend structure absorbed additions with no friction.**  
Adding sort params, a new `/audit-log/actors` endpoint, and optional query params to two routers required only targeted edits. No existing tests broke. The router architecture — thin routers, shared `_build_filters` helpers, Pydantic response models — made extension cheap. Worth preserving and codifying as a convention.

**TypeScript strict mode caught issues immediately.**  
Every change to `types/index.ts` and the hook files produced immediate compile errors when downstream pages didn't match. `pnpm tsc --noEmit` as a fast check was the right verification step. The type boundary between `CaseFilters`/`AuditFilters` and the hook layer held up correctly under extension.

**Tri-state sort design was right the first time.**  
The `SortState = { by; dir } | null` union type cleanly represented all three states (unsorted, asc, desc) without separate nullable fields. No rework needed.

**The AI reviewer's parse-failure escalation was the right fallback.**  
When the model returned fenced JSON, the classifier escalated rather than crashing or silently doing the wrong thing. The fallback note in the decision text made the bad records easy to identify and delete. Defensive-by-default behaviour in the classifier paid off.

---

## What Could Have Gone Better

**1. AI reviewer approve/reject semantics were inverted from day one.**  
The system prompt defined `approve` as "content violates policy, action it" and `reject` as "false positive, no action." The code's `ACTION_TO_STATUS` mapping treats `approve → approved` (case cleared) and `reject → rejected` (content removed). The two conflicted completely. The AI was approving harmful content throughout the first review run.

*Root cause:* No one reviewed the system prompt for semantic correctness. The implementer wrote it; the reviewer checked code, not prompt logic. There was no prompt-review step in the sequence.

*What would have prevented it:* A checklist item in the reviewer role for AI-adjacent features: "verify that prompt action labels match the system's action semantics." Alternatively, a new resource on prompt design with this as a named convention.

**2. Dev server started without `--reload`, causing a false debugging detour.**  
The implementer output explicitly shows the correct command: `uvicorn app.main:app --reload --port 8000`. In practice, `--reload` was omitted. When sort params and the actors endpoint were added, the running server didn't pick them up. The symptom — "sort not working" — looked like a frontend or API logic bug, leading to unnecessary investigation before the stale server was identified.

*Root cause:* No enforcement or scripting of the dev startup command. The correct command is buried in the implementer output's "How to Run" section.

*What would have prevented it:* A `dev.sh` or `Makefile` target in the project that starts the API with `--reload`. The implementer should produce this as a deliverable, not just document the command in prose.

**3. Actor filter started as a text input; should have been a dropdown.**  
The first implementation used a free-text input + submit for the actor ID filter. The user immediately asked for a dropdown of actual actors. This required a new API endpoint (`/audit-log/actors`) and a frontend hook — straightforward, but the initial design was wrong.

*Root cause:* The universe of actors is small and DB-queryable, but the design treated it as open-ended input. Text inputs are for open-ended user strings; dropdowns are for known, queryable enumerables.

*What would have prevented it:* A UI pattern principle: when a filter targets a queryable set (actor IDs, DB-backed enums), use a data-driven dropdown rather than a text field.

**4. Retro ran one session late.**  
The retro should have run immediately after the reviewer's verdict (end of session 1). Instead, it was deferred until after a second session of feature work. The retro is now covering two phases simultaneously and some early findings are harder to reconstruct.

*Root cause:* The reviewer's Handoff section named "next role: retro" but the sequence wasn't checked at the start of session 2 before new work began.

*What would have prevented it:* Enforcing the session start protocol step: read `project-state.md` and check whether a sequence is in-flight before starting new work.

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| Retro | Full implementer output loaded (166 lines) for a completed project | Low | Acceptable — file is appropriately sized. Add a Summary section to future implementer outputs so retro can read that first and drill in only if needed. |
| Session 2 (feature work) | No role context loaded — direct ad-hoc implementation | N/A | Correct for a small `add-feature` scope. Full routing would have been overhead. |

### Redundancy Patterns

`project-state.md` "Project File Map" duplicates the implementer's "Files Produced" table. This is useful as a workspace reference, but it will drift as features are added (e.g. `audit.ts` gained `useAuditActors` in session 2 but the file map doesn't reflect it). In future projects, `project-state.md` should link to the implementer output rather than re-listing every file.

### Scoping Recommendations

- Implementer outputs should open with a **Summary** section (1 paragraph: what was built, key deviations, critical gaps). Retro and reviewer can read the summary first and only load the full file for specific findings.
- `vibecoding-style.md` is loaded by most roles but referenced lightly. Consider moving the "vibe mode vs structured mode" section to `routing.md` (where sequence selection happens) and keeping `vibecoding-style.md` focused on collaboration and code preferences only.

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `resources/vibecoding-style.md` | Add under Code Preferences: "UI filters: use a data-driven dropdown for any filter targeting a queryable set (actor IDs, DB-backed enums). Use text input only for open-ended user strings." | Prevents the actor-filter rework pattern | No |
| `resources/typescript-conventions.md` | Add same principle as a TS-specific note with a concrete example (actor dropdown backed by a `useXActors` hook) | Language-specific grounding for the same principle | No |

### Skills to Update

No existing skills require changes. One new skill recommended (see below).

### Routing Changes

| Sequence | Change | Reason | Human decision required? |
|----------|--------|--------|--------------------------|
| `new-project-full`, `add-feature` | Reviewer role: add checklist item — "If the project includes an LLM system prompt, verify that each action label in the prompt matches the system's action semantics (e.g. what `approve` maps to in `models.py`)" | The approve/reject inversion was invisible to standard code review; it requires prompt-specific scrutiny | No |
| All sequences | Session start protocol (CLAUDE.md step 6 or routing.md): "Check `project-state.md` for any sequence in-flight. If a sequence is in-flight, the next role in that sequence must run before new work begins, unless the human explicitly overrides." | Retro ran one session late; in-flight state was not checked | No |

### New Resources or Skills Needed

**`resources/prompt-design.md`**  
Conventions for writing LLM system prompts in this workspace. Minimum content:
1. Action labels must be validated against the system's enum values and their semantic meaning in the code (e.g. `approve` in the prompt must mean what `approve` means in `ACTION_TO_STATUS`).
2. When action semantics are non-obvious (approve/reject/escalate in a T&S context can mean different things to different people), include a one-line worked example per action in the prompt.
3. Use `escalate` as the safe fallback action, not `approve`.

Load in: implementer (when writing prompts), reviewer (to check prompt semantics).

**`skills/dev-server-setup.md`**  
How to start the dev stack for a FastAPI + Vite project. Covers: uvicorn with `--reload`, Vite dev command, docker-compose for Postgres, and the rule: "Any backend code change requires `--reload` to be active, or the server must be restarted manually." The implementer should produce a `Makefile` or `dev.sh` using this skill so the correct startup command is one target, not a prose paragraph.

Load in: implementer (to produce the startup script), reviewer (to verify `--reload` is present).

---

## One Change to Make Now

**Create `resources/prompt-design.md`** with the three conventions above, and add a row to the reviewer step in `new-project-full` and `add-feature`: load `prompt-design.md` when the project includes an LLM prompt.

**Why this one:** The approve/reject inversion caused real data corruption — wrong decisions were written to the DB and required manual cleanup. It was invisible to standard code review because it's a semantic error in a string constant, not a type or logic error. A single resource with one named convention ("action labels must match system semantics") would have caught it at implementation time. The other findings (stale server, text input vs dropdown) are friction; this one produced bad data.

**Exact change:**
1. Create `resources/prompt-design.md` with the three conventions.
2. In `resources/routing.md`, add to the reviewer step of `new-project-full` and `add-feature`: Resources column gets `prompt-design.md (if project includes LLM prompts)`.

---

## Handoff

Recommended actions, ordered by value:

1. **Create `resources/prompt-design.md`** — prevents data-corrupting bugs in AI features.
2. **Create `skills/dev-server-setup.md`** — eliminates the stale-server debugging class of mistake.
3. **Update `resources/vibecoding-style.md`** and `resources/typescript-conventions.md` — add UI filter pattern (dropdown vs text input).
4. **Update `resources/routing.md`** — add reviewer LLM checklist item and session-start in-flight check.

Update `_config/project-state.md` to record that the retro ran and which recommendations were applied.
