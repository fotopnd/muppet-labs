## Brief — 2026-06-07

### Active Projects

**red-team-platform** — Full build complete (PASS WITH NOTES); attack session is the only remaining action before this project has real data.
- Next action: Spin up RunPod RTX 4090 spot pod, pull gemma2:9b (~3 min), set `OLLAMA_BASE_URL` in `.env`, run Phase 1 wave loop — full plan at `resources/runpod-plan.md`. ~$0.50 total, ~40 min on pod.
- Blocker: Need to bring llm-safety-monitor down first (port 5435 conflict) before `docker compose up` for red-team infra.

**error-hide-seek** — Full build complete today (PASS WITH NOTES); stack ready for first real experiment on ports 5436/8004/5174.
- Next action: `docker compose up -d db` → `uv run fetch-corpus` (200 papers from arxiv) → `uv run plant-errors --experiment-id 1` → open UI at localhost:5174 and do 5–10 review sessions → `uv run score --experiment-id 1`. Claude API cost: ~$0.63 for 100 papers.
- Note: Keep a separate experiment ID for any test sessions — each `POST /sessions` on a human_agent paper fires a blue-team API call.

**llm-safety-monitor** — Pipeline live with 3 trained classifiers; one tab short of complete.
- Next action: Add Model Disagreement tab — endpoint `/metrics/disagreements` already exists. ~1h frontend work: new route, `useDisagreements` hook, table component. No backend changes needed.

**moderation-dashboard** — Complete and parked; waiting on deploy slot.
- Next action: None until P4 (writeups). Then `gh repo create` + Hostinger VPS deploy as a batch with the other projects.

---

### Tomorrow's Recommended Session Order

Run these in parallel where possible:

1. **RunPod attack session** — start the pod, kick off Phase 1, let it run (~25 min unattended). While it runs, do step 2.
2. **error-hide-seek experiment** — fetch corpus + plant errors while attack session runs on RunPod. Then do review sessions.
3. **Model Disagreement tab** — quick frontend session, ~1h, closes llm-safety-monitor.

By end of tomorrow: all three active projects have real data. Writeups unblock.

---

### Next Up from Ideas Queue

**Portfolio writeups (P4)** — All builds are done. The only remaining gap before writeups is real experiment data from red-team (P1) and error-hide-seek (P2). Once those numbers exist, each project needs a writeup framed for a Safeguards hiring manager. Priority order: error-hide-seek (headline uplift ± CI), red-team platform (ASR by strategy + cluster themes), llm-safety-monitor (F1 table, live pipeline story).
- To start: after P1 + P2 complete, invoke `write-doc` sequence for error-hide-seek first (freshest build, most differentiated piece).

**Constitutional Classifiers (new build, P3 ideas queue)** — Dynamic constitutional evaluator API: accept a constitution doc + text, score against it, benchmark vs jailbreak variants. Closes the "flexible alignment layer" angle not covered by the existing stack.
- To start: only after writeups are in progress. If wanting a new build session before writeups, this is the one.

---

### Flags

No blocking decisions required. Everything is sequenced and unblocked.

RunPod requires a $10 minimum credit deposit if the account has zero balance — do this before starting tomorrow's session (~2 min at runpod.io/console/billing).
