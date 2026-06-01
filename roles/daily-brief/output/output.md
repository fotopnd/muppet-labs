# daily-brief

**Role:** daily-brief  
**Date:** 2026-06-02  
**Reads:** `resources/priorities.md`, `resources/project-status.md`, `_config/project-state.md`, `resources/project_ideas.md`

---

## Brief — 2026-06-02

### Active Projects

**Case Queue (project 21)** — Code complete, all tests passing, UI enhancements and AI reviewer
bug fixed this session. Not yet deployed.
- Next action: Run `fly launch --no-deploy && fly deploy` from `projects/case-queue/api` to
  deploy the API to Fly.io, then `vercel deploy --prod` from `projects/case-queue/web`.
  Full command sequence in `resources/project-status.md` → How to Deploy.
- Blocker: This is the only thing standing between the current state and a live portfolio URL.
  Everything else is ready.

**Eval Harness (project 2)** — Complete, 45 tests passing, baseline runs committed.
Published to GitHub is held pending case-queue going live.
- Next action: Once case-queue is deployed, run `gh repo create muppet-labs-eval-harness --public`
  and push. Then update `resources/project-status.md` with the live URL.

### Next Up from Ideas Queue

**Project 11 — Account Security Anomaly Dashboard** — First unstarted project after the two
deploy/publish actions. Directly translates 18 months of Meta account security DE experience
into a public artefact using the LANL Cyber Dataset or CERT Insider Threat data. Closes the
dbt gap and the account security domain gap simultaneously — strong signal for the DE role.
- To start: Run the `brief` role with this prompt: "Project 11 — Account Security Anomaly
  Dashboard. Target: DE Safeguards. Stack: Python, dbt, SQL. See project_ideas.md #11 for
  full description."

### Flags

- **Deploy case-queue now or defer?** The deploy requires interactive CLI steps (`fly auth login`,
  `vercel login`). If you want to do it this session, run `! fly auth login` and
  `! vercel login` in the prompt, then follow the How to Deploy steps. If deferring, note it
  in `project-state.md` so the next brief doesn't repeat it as urgent when it isn't.
