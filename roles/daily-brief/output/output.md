## Brief — 2026-06-03 (evening)

### Active Projects

**Case Queue (project 21)** — Code complete (22/22 tests, README, deploy artifacts ready); not yet on GitHub or live. This is the single blocker between you and submitting the SWE Safeguards application.
- Next action: `gh repo create case-queue --public --source=projects/case-queue --push`, then SSH to Hostinger VPS and run the Docker Compose deploy sequence from `resources/project-status.md` (§ How to Deploy).

**Toxicity Classifier — project 8** — DistilBERT fine-tuning COMPLETE (F1=0.8473, AUC-ROC=0.9241, checkpoint at `resources/models/toxicity-classifier-finetuned/distilbert-best`). RoBERTa overnight run is queued and ready.
- Next action (do this before bed, ~6h unattended): plug in, then from `projects/toxicity-classifier-finetuned/`:
  ```
  caffeinate -i uv run train --model roberta --output-dir checkpoints --epochs 4 --batch-size 32
  ```
- After run: evaluate → move checkpoint to `resources/models/toxicity-classifier-finetuned/roberta-best` → set `ROBERTA_CHECKPOINT_PATH` in `projects/moderation-stream/.env`.

**Moderation Stream (project 22)** — Phase 1 complete (21/21 tests); Phase 2 consumers stubbed and waiting on RoBERTa checkpoint. Deploys to the same Hostinger VPS as case-queue.
- Next action: deploy alongside case-queue (add nginx rule for port 8001, run `alembic revision --autogenerate -m "initial"` against live DB). Real Jigsaw `train.csv` must be present on VPS for the producer.

**Eval Harness (project 2)** — Complete (45/45 tests); held until portfolio is stable.
- Next action: `gh repo create muppet-labs-eval-harness --public` and push — do this immediately after case-queue is live (~30 min).

---

### Next Up from Ideas Queue

**Project 8 post-RoBERTa write-up** — Once the overnight run completes, run the `write-doc` sequence to produce a technical summary (zero-shot vs fine-tuned comparison, per-category breakdown). This closes the "partial" PyTorch signal in the portfolio and completes the project 8 deliverable.
- To start (tomorrow morning): run `uv run evaluate --model roberta --checkpoint-dir checkpoints/roberta-best`, then invoke `doc-brief` → `author` → `doc-reviewer` with the experiment results.

---

### Flags

**Housekeeping:** `resources/project-status.md` is stale for project 8 — it still lists DistilBERT weights as "not produced." Update it after the RoBERTa run completes (one pass covering both models).

**Decision this session:** Start RoBERTa run tonight, or deploy case-queue first? Both are independently actionable. Deploying case-queue (~1–2h of SSH + config work) unblocks the job application now. Starting the RoBERTa run costs ~2 minutes of setup and then runs overnight without attention. Recommend: kick off the RoBERTa run first (2 min), then tackle the deploy.
