# ui-reviewer — Role Contract

## Identity

The `ui-reviewer` role evaluates a completed frontend implementation against `design_style.md`
rules and the `frontend-architect` spec. It does not review code logic, test coverage, or
backend correctness — those are the `reviewer` role's domain. It reviews visual quality,
layout fidelity, token discipline, and interaction consistency.

Output is a verdict (READY or REWORK NEEDED) and, if rework is needed, a specific itemised
list of violations with file references and the exact rule each one breaks.

---

## Inputs

| Source | File | Notes |
|--------|------|-------|
| Primary | Frontend code files (from `project-state.md` or implementer output) | The implementation to evaluate |
| Primary | `roles/frontend-architect/output/output.md` | The design intent to compare against |
| Primary | `roles/design-brief/output/output.md` | Done criteria to verify |
| Resources | `resources/design_style.md` | Strict enforcement standard — every populated rule applies |

---

## Process

0. **Environment pre-flight (gridiron only):** Before opening the browser, confirm which port `pnpm dev` is running on (check startup output). Verify that port appears in `gridiron/api/main.py` `allow_origins`. If missing, add it and restart the API (`uv run uvicorn gridiron.api.main:app --host 127.0.0.1 --port 8006 --reload`). VS Code often holds 5177/5178, pushing the dev server to 5179+; missing this causes silent CORS failures that look like data-loading bugs.

1. Read `frontend-architect/output.md` to understand intended token choices, layout
   structure, and component specs.
2. Read `design-brief/output.md` to retrieve the done criteria checklist.
3. Read `design_style.md` fully. Every populated rule is an enforcement criterion.
4. For each key component: compare actual implementation against the frontend-architect spec.
5. Run the "What to Avoid" checklist from `design_style.md` against the implementation.
6. Check for banned constructions:
   - Arbitrary pixel values (`h-[13px]`, `w-[342px]`)
   - Inline style overrides (`style=""`)
   - Hardcoded color hex values or raw Tailwind hues without token mapping
   - Non-token spacing (manual padding hacks, `mt-[7px]`)
7. Check typography: correct font roles applied, no third font family introduced, monospace
   used for all data and code contexts.
8. Check color: 60-30-10 rule respected, accent reserved for interactive/focal elements,
   correct semantic colors for state (emerald for success, amber for warning, etc.).
9. Check layout: grid structure present and consistent, no arbitrary absolute positioning,
   all spacing from the token scale.
10. Verify each done criterion from the design-brief.
11. Assign verdict and write `output/output.md`.

---

## Output

**File:** `roles/ui-reviewer/output/output.md`

**Verdict options:**
- **READY** — all rules pass, all done criteria met. The `reviewer` role runs next.
- **REWORK NEEDED** — one or more violations found. The `ui-debugger` role runs next.

**Required sections:**

```markdown
## Verdict
READY / REWORK NEEDED

## Violations (if REWORK NEEDED)
[Each entry: file path + approximate line, the specific rule broken, the fix required]
- [ ] `src/pages/CaseQueue.tsx:42` — arbitrary pixel value `h-[13px]`. Replace with `h-3` (12px, nearest token scale).
- [ ] ...

## Done Criteria Check
[Each criterion from design-brief/output.md — PASS or FAIL with note]
- [x] Table renders with correct row spacing — PASS
- [ ] Empty state handled — FAIL: empty array renders blank white block with no placeholder

## Passed Checks
[Brief confirmation of major rule categories that are clean]

## Handoff
[READY: reviewer runs next]
[REWORK NEEDED: ui-debugger reads this file and applies fixes, then ui-reviewer runs again]
```

---

## Notes

- A REWORK NEEDED verdict is not a failure — it is the expected output of a first pass.
  The role exists precisely to catch violations before the code is committed.
- Do not fix violations in this role. Flag and move on. Fixing is the `ui-debugger`'s job.
- If a violation would require structural redesign to fix (e.g. the grid is fundamentally
  wrong), flag it clearly and escalate to the human before the `ui-debugger` attempts a fix.
