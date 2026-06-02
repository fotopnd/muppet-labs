# daily-brief

**Role:** daily-brief  
**Date:** 2026-06-02  
**Reads:** `resources/priorities.md`, `resources/project-status.md`, `_config/project-state.md`, `resources/project_ideas.md`

---

## Brief — 2026-06-02

### Active Projects

**Case Queue (project 21)** — Code complete, all features shipped (sort, filters, AI reviewer fix, retro done). Fly.io and Vercel configs committed and ready. Not yet deployed.
- Next action: Run `fly auth login`, then `fly launch --no-deploy && fly deploy` from `projects/case-queue/api`. Then `vercel deploy --prod` from `projects/case-queue/web`. Full step-by-step in `resources/project-status.md` → How to Deploy.
- Blocker: Interactive CLI login steps (`fly auth login`, `vercel login`) must be run by you. Use `! fly auth login` in the prompt to run them in this session.

**Eval Harness (project 2)** — Complete (45/45 tests, baseline runs committed, README done). Held until case-queue is live and the portfolio URL is confirmed.
- Next action: Once case-queue is deployed, run `gh repo create muppet-labs-eval-harness --public` and push.

### Next Up from Ideas Queue

**Project 11 — Account Security Anomaly Dashboard** — First unstarted project after the two deployment actions. Directly translates 18 months of Meta account security DE experience into a public artefact (LANL Cyber Dataset or CERT Insider Threat data). Closes the dbt gap and the account security domain gap simultaneously — high-value signal for the DE role.
- To start: Run the `brief` role with: *"Project 11 — Account Security Anomaly Dashboard. Target: DE Safeguards. Stack: Python, dbt, SQL. See project_ideas.md #11."*

### Flags

- **Deploy today?** Everything is ready. The only step left is running the CLI login commands. If you want to do this now: `! fly auth login` and `! vercel login`, then follow the deploy sequence in `resources/project-status.md`. If deferring, it stays the top priority next session.
