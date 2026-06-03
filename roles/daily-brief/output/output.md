## Brief — 2026-06-03

### Active Projects

**Case Queue (project 21)** — Code complete (22/22 tests, README, deploy artifacts ready); not yet on GitHub or live.
- Next action: `gh repo create case-queue --public --source=projects/case-queue --push`, then SSH to Hostinger VPS and run the Docker Compose deploy sequence in `resources/project-status.md` (§ How to Deploy). This unblocks the application.
- Note: deploy target is Hostinger VPS (not Fly.io — that config exists but is superseded).

**Eval Harness (project 2)** — Complete (45/45 tests, baseline runs committed, README done); held pending portfolio stability.
- Next action: `gh repo create muppet-labs-eval-harness --public` and push — do this immediately after case-queue is live. ~30 min.

**Moderation Stream (project 22)** — Phase 1 complete (21/21 tests, technical summary written); deploys to the same Hostinger VPS as case-queue.
- Next action: deploy alongside case-queue. Add `VITE_STREAM_API_URL` to `.env` on VPS, add nginx proxy rule for port 8001, and run `alembic revision --autogenerate -m "initial"` against live DB before first start.

---

### Next Up from Ideas Queue

**Project 8 — Fine-Tuned Toxicity Classifier** — first unstarted project after deploy + publish. Closes the PyTorch gap (last open hard gap in the portfolio) and activates moderation-stream Phase 2 by dropping two checkpoint files into config — no rebuild needed.
- To start: run the `brief` role with: *"Project 8 — Fine-Tuned Toxicity Classifier. Stack: Python, PyTorch, HuggingFace. Fine-tune DistilBERT and RoBERTa on Jigsaw Toxic Comments. Output: two checkpoint files for project 22 Phase 2. See project_ideas.md #8."*

---

### Flags

**Deploy or build this session?** The portfolio is application-ready the moment case-queue is live on Hostinger. Deploying today means you can submit this week. Starting project 8 instead keeps the application on hold. No wrong answer — confirm which you want to tackle.
