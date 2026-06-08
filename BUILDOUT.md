# Portfolio Buildout Plan

Master execution plan for the Anthropic Safeguards portfolio.
Detailed GPU setup in `resources/runpod-plan.md`. GPU pricing in `resources/runpod-pricing.md`.

---

## State of the portfolio

| Layer | Code | Migrations | Data / execution |
|---|---|---|---|
| `llm-safety-monitor` | ✓ complete | ✓ written — needs `upgrade head` | needs `uv sync` |
| `llm-safety-classifier` (shared) | ✓ complete | — | needs `uv sync` in both projects |
| `red-team-platform` | ✓ complete | ✓ written — needs `upgrade head` | **attack sweep not yet run** |
| `error-hide-seek` | ✓ complete | ✓ written — needs `upgrade head` | **experiment not yet run** |
| Model checkpoints | ✓ trained — pair/prompt/taxonomy at `resources/models/` | — | — |

---

## Execution sequence

### 0. Install shared package (local, ~2 min)

```bash
cd ~/Documents/muppet-labs/projects/llm-safety-monitor && uv sync
cd ~/Documents/muppet-labs/projects/red-team-platform  && uv sync
```

Installs `llm-safety-classifier` as an editable local package in both venvs.

---

### 1. Migrate both databases (local, ~2 min)

Red-team and monitor use separate Postgres instances. Bring each up and migrate:

```bash
# Red-team (port 5433)
cd ~/Documents/muppet-labs/projects/red-team-platform
docker compose up -d
uv run alembic upgrade head   # applies 001 (if fresh) + 002 (outbox)

# Monitor (port 5434) — can be up simultaneously, different port
cd ~/Documents/muppet-labs/projects/llm-safety-monitor
docker compose up -d
uv run alembic upgrade head   # applies 001–004 (classifier_version + dedup)
```

**Port map (no conflicts):**

| Service | Host port |
|---|---|
| Monitor Postgres | 5434 |
| Red-team Postgres | 5433 |
| Error-hide-seek Postgres | 5436 |
| Kafka | 9092 |

---

### 2. Red-team attack sweep (RunPod, ~40 min, ~$0.33)

**What it produces:** 1,800 `Run` rows in red-team DB, outbox rows for the monitor feed, `benchmarks/results.md` populated with real ASR numbers.

**Prerequisites:**
- red-team docker stack up and migrated (step 1)
- pair classifier checkpoint exists at `resources/models/llm-safety-monitor/pair-2026-06-07/config.json`
- `.env` has `PAIR_CLASSIFIER_PATH` and `OLLAMA_MODEL=gemma2:9b`

**RunPod setup (see `resources/runpod-plan.md` for detail):**

```bash
# 1. Start a RunPod RTX 4090 pod with Ollama template
# 2. On pod terminal:
ollama pull gemma2:9b
# 3. Copy proxy URL (https://<id>-11434.proxy.runpod.net)
# 4. Update .env:
OLLAMA_BASE_URL=https://<id>-11434.proxy.runpod.net
OLLAMA_MODEL=gemma2:9b
```

**Seed corpus (local, one-time, ~4 min):**
```bash
cd ~/Documents/muppet-labs/projects/red-team-platform
uv run seed-corpus
```

**Phase 1 sweep — 6 strategies × ~300 goals:**
```bash
for strategy in DAN evil_system_prompt refusal_suppression combination_1 few_shot_json AIM; do
    echo "=== $strategy ===" && uv run attack --strategy "$strategy"
done
```

**Post-sweep:**
```bash
uv run cluster          # K-means on jailbreak response text
cd web && pnpm dev      # review StrategyComparison + CoverageHeatmap
```

**Stop the RunPod pod immediately after.**

**Feed results into monitor:**
```bash
# Monitor stack must be running (Kafka + Postgres + consumers)
cd ~/Documents/muppet-labs/projects/red-team-platform
uv run outbox-publisher     # runs until all rows published, then exit
```

**Fill in results:**
After reviewing the dashboard, update `projects/red-team-platform/benchmarks/results.md` with actual ASR numbers per strategy.

**Estimated time:** ~25 min sweep + ~10 min cluster/review + ~5 min publish = ~40 min GPU time.
**GPU cost:** RTX 4090 spot @ ~$0.50/hr × 0.7hr = **~$0.35**

---

### 3. Error-hide-seek experiment (local + Anthropic API, ~30 min, ~$1.10)

**What it produces:** Per-category TPR across 3 conditions, `results/findings.md` populated, blue-team parse failure rate.

**Prerequisites:**
- error-hide-seek docker stack up and migrated
- `ANTHROPIC_API_KEY` set in `projects/error-hide-seek/.env`

**Setup:**
```bash
cd ~/Documents/muppet-labs/projects/error-hide-seek
docker compose up -d
uv run alembic upgrade head
```

**Step 1 — Fetch 100 arXiv papers (~5 min, free):**
```bash
uv run fetch-corpus --count 100
# Rate-limited to 0.4s between requests — fully automatic
```

**Step 2 — Create experiment (assigns conditions + intended_category via seeded shuffle):**
```bash
# Get paper IDs from DB, then:
curl -s -X POST http://localhost:8004/experiments \
  -H "Content-Type: application/json" \
  -d '{"name":"exp-1","description":"Phase 3 uplift measurement","paper_ids":[1,2,...,100]}'
# Returns experiment_id (will be 1 on a fresh DB)
```

**Step 3 — Plant errors (~10 min, ~$0.56 API cost):**
```bash
uv run plant-errors --experiment-id 1
# 100 Claude API calls (sonnet-4-6)
# ~700 tokens in + ~200 tokens out per paper
# Idempotent — safe to re-run if interrupted
```

**Step 4 — Run blue-team sessions for AGENT_ONLY + HUMAN_AGENT (~10 min, ~$0.51 API cost):**
```bash
# Start the API
uv run api &

# Create sessions for all papers via the API
# AGENT_ONLY sessions auto-complete (no human needed)
# HUMAN_AGENT sessions need human review via the web UI
cd web && pnpm dev
# Navigate to each HUMAN_AGENT session and submit detections
```

**Step 5 — UNAIDED sessions (manual, via UI):**
For each UNAIDED paper, submit a review (with or without detections) to close the session.

**Step 6 — Score and report:**
```bash
uv run score --experiment-id 1
# Prints TPR table per condition + uplift
# Copy results into projects/error-hide-seek/results/findings.md
```

**Anthropic API cost breakdown:**

| Step | Calls | Input tokens | Output tokens | Cost |
|---|---|---|---|---|
| plant-errors (100 papers, 10% retry) | ~110 | ~77k | ~22k | ~$0.56 |
| annotate AGENT_ONLY (~33 papers) | ~37 | ~30k | ~11k | ~$0.25 |
| annotate HUMAN_AGENT (~33 papers) | ~37 | ~30k | ~11k | ~$0.25 |
| **Total** | **~184** | **~137k** | **~44k** | **~$1.06** |

Prices at claude-sonnet-4-6 rates: $3.00/MTok input, $15.00/MTok output.

---

### 4. Model retraining (optional — RunPod, ~33 min, ~$0.25)

The existing checkpoints (`pair-2026-06-07`, `prompt-2026-06-07`, `taxonomy-2026-06-07`) are trained. Retrain if:
- Red-team sweep reveals high-ASR harm categories → add targeted WildGuard training data
- Architecture upgrade to DeBERTa-v3-base or ModernBERT-base
- Want to demonstrate training provenance in the portfolio

**When to retrain (decision criteria):**
1. After the sweep, if any harm category shows ASR > 50% across 3+ strategies → that category is underrepresented in training data
2. If the portfolio needs a training script as an artefact (currently training is undocumented in the repo)

**Baseline retrain (same RoBERTa-base, fresh run on updated WildGuard):**

```bash
# On RunPod A10G pod — see resources/runpod-plan.md
cd ~/llm-safety-monitor-training
uv run train-pair     --output-dir /workspace/pair     --epochs 4
uv run train-prompt   --output-dir /workspace/prompt   --epochs 4
uv run train-taxonomy --output-dir /workspace/taxonomy --epochs 4

# Rsync checkpoints back (each ~500 MB, ~1-2 min total):
rsync -avz root@<pod-ip>:/workspace/pair/ \
  ~/Documents/muppet-labs/resources/models/llm-safety-monitor/pair-$(date +%F)/
```

**Architecture upgrade options:**

| Model | Params | M4 step time | A10G step time | Pair run (50k, 4ep) | A10G cost |
|---|---|---|---|---|---|
| RoBERTa-base (current) | 125M | 1.4s | ~0.25s | ~21 min | ~$0.16 |
| ModernBERT-base | 149M | 2.3s | ~0.30s | ~25 min | ~$0.19 |
| DeBERTa-v3-base | 184M | 35s (unusable) | ~0.6s | ~55 min | ~$0.41 |

**DeBERTa recommendation:** Use A100 40GB spot (~$1.24/hr) for DeBERTa. Step time ~0.25s → pair run ~23 min → ~$0.48. Disproportionate performance gain (~6-8% F1 over RoBERTa on safety classification benchmarks) for ~$0.30 extra.

**After retraining:**
1. Copy new checkpoints to `resources/models/llm-safety-monitor/<model>-$(date +%F)/`
2. Update `.env` in both monitor and red-team with new paths
3. Bump version in `packages/llm-safety-classifier/pyproject.toml`
4. `uv sync` in both projects — `get_version()` will return the new version
5. `classifier_version` in new DB rows will reflect the bump automatically

---

## Total cost summary

| Run | Where | Time | Cost |
|---|---|---|---|
| Step 0: uv sync | local | 2 min | free |
| Step 1: migrations | local | 2 min | free |
| Step 2: attack sweep | RunPod RTX 4090 spot | ~40 min | ~$0.35 |
| Step 3: error-hide-seek experiment | local + Anthropic API | ~30 min | ~$1.06 |
| Step 4a: baseline retrain (optional) | RunPod A10G spot | ~33 min | ~$0.25 |
| Step 4b: DeBERTa upgrade (optional) | RunPod A100 40GB spot | ~23 min | ~$0.48 |
| **Minimum (steps 0–3)** | | **~75 min** | **~$1.41** |
| **Recommended (+ baseline retrain)** | | **~110 min** | **~$1.66** |
| **Full (+ DeBERTa upgrade)** | | **~133 min** | **~$1.89** |

---

## What the results unlock

| Run | What it fills in |
|---|---|
| Attack sweep | `benchmarks/results.md` ASR per strategy; monitor Disagreements tab shows red-team misses |
| Cluster | qualitative failure themes for red-team README / portfolio narrative |
| error-hide-seek experiment | `results/findings.md` per-category TPR and uplift; validates 3-condition RCT |
| Model retrain | new `classifier_version` in DB; before/after F1 comparison in monitor dashboard |

---

## Pre-run checklist

- [ ] `resources/models/llm-safety-monitor/pair-2026-06-07/config.json` exists
- [ ] `resources/models/llm-safety-monitor/taxonomy-2026-06-07/config.json` exists
- [ ] `projects/red-team-platform/.env` has `PAIR_CLASSIFIER_PATH` (absolute path)
- [ ] `projects/red-team-platform/.env` has `OLLAMA_MODEL=gemma2:9b`
- [ ] `projects/error-hide-seek/.env` has `ANTHROPIC_API_KEY`
- [ ] RunPod account funded (minimum $10 deposit covers all runs above)
- [ ] `uv sync` done in both projects (step 0)
- [ ] Migrations applied (step 1)
