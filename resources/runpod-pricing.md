# RunPod — M4 Offload Strategy

**Philosophy:** Use RunPod for any job that would tie up the M4 for more than ~1h. Target: spend $1-2 in credits, offload 4-10h of local compute, get results back in under 1h.

RunPod is for **training runs and batch simulation jobs only.** Production deployment stays on Hostinger VPS.

---

## Current Jobs to Offload

| Job | M4 time (actual/est) | RunPod GPU | RunPod time | Cost | Priority |
|-----|---------------------|-----------|-------------|------|----------|
| red-team attack session (3,000 attacks, gemma2:9b) | ~4-5h | RTX 4090 spot | ~40 min | ~$0.50 | **P1 now** |
| Re-train all 3 RoBERTa classifiers (4 epochs each) | ~4.5h (actual) | A10G spot | ~55 min | ~$0.41 | If re-run needed |
| **Total** | | | | **~$0.91** | |

---

## Future Jobs Worth Offloading

These are not yet scheduled but are the natural next training experiments:

| Job | Why | M4 estimate | RunPod GPU | RunPod time | Cost |
|-----|-----|-------------|-----------|-------------|------|
| Scale pair classifier to full 376k samples (vs 50k cap) | More training data → better F1. Currently capped because 376k × 4 epochs ≈ 10h on M4. | ~10h | A10G spot | ~2.2h | ~$1.00 |
| Re-train with 4 epochs (currently defaulting to 2 in scripts) | Prompt + taxonomy scripts default `epochs=2`; the 4.5h run used `--epochs 4` explicitly | ~4.5h | A10G spot | ~55 min | ~$0.41 |
| DeBERTa-v3-base (better than RoBERTa, killed locally at 35s/step) | ~6-8% better on safety classification benchmarks. Completely infeasible on M4 MPS. | **Would never finish** (35s/step) | A100 40GB spot | ~2.5h | ~$3.10 |
| ModernBERT-base (2.26s/step on MPS) | Newer architecture, potentially better on short safety texts | ~3× pair run = ~7h | A10G spot | ~1.5h | ~$0.68 |
| error-hide-seek: large-scale experiment (500+ papers) | More data = more statistical power for uplift measurement. Not GPU — Anthropic API. | N/A | N/A — API cost | — | ~$3.50 (API) |

---

## GPU Selection Guide

### For Ollama inference (attack session, gemma2:9b)

gemma2:9b Q4_K_M = ~5.5 GB VRAM. Any 24 GB card works. 4090 is the fastest.

| GPU | Tok/s | Phase 1 (1,800 atk) | Both phases (3,000) | Spot $/hr | Total |
|-----|-------|--------------------|--------------------|-----------|-------|
| RTX 3090 | ~75 | ~30 min | ~50 min | ~$0.28 | ~$0.23 |
| **RTX 4090** | **~110** | **~25 min** | **~40 min** | **~$0.50** | **~$0.33** |
| A10G | ~80 | ~28 min | ~47 min | ~$0.45 | ~$0.35 |

**Pick: RTX 4090 spot.** See `resources/runpod-plan.md` for full setup.

---

### For RoBERTa-base training (125M params, batch=32, max_len=128)

M4 MPS baseline: **1.35-1.46 s/step**. CUDA speedup over MPS for this model: 5-8×.

| GPU | VRAM | Step time (est) | Pair (50k, 4ep) | Prompt (4ep) | Taxonomy (4ep) | All 3 | Spot $/hr | Cost |
|-----|------|----------------|----------------|-------------|---------------|-------|-----------|------|
| T4 | 16 GB | ~0.45s | ~38 min | ~10 min | ~10 min | ~58 min | ~$0.16 | ~$0.15 |
| **A10G** | **24 GB** | **~0.25s** | **~21 min** | **~6 min** | **~6 min** | **~33 min** | **~$0.45** | **~$0.25** |
| A100 40GB | 40 GB | ~0.12s | ~10 min | ~3 min | ~3 min | ~16 min | ~$1.24 | ~$0.33 |

**Pick: A10G spot.** T4 is the budget pick (~$0.15 total) but VRAM is tighter for larger batch experiments. A10G is fast and comfortable for ~$0.25. A100 is overkill for 125M params.

---

### For DeBERTa-v3-base or ModernBERT (if you want to try larger models)

DeBERTa-v3-base: 184M params. ModernBERT-base: 149M params.

| GPU | DeBERTa step time | Pair run (50k, 4ep) | Spot $/hr | Cost |
|-----|------------------|--------------------|-----------|----- |
| A10G | ~0.6s | ~55 min | ~$0.45 | ~$0.41 |
| **A100 40GB** | **~0.25s** | **~23 min** | **~$1.24** | **~$0.48** |
| A100 80GB | ~0.18s | ~17 min | ~$1.99 | ~$0.60 |

**Pick: A100 40GB spot** for DeBERTa. The step time difference vs A10G is significant for larger models, and the cost difference is only ~$0.07 for a single run.

---

## Workflow: Getting Data On and Off RunPod

### Datasets — let the pod download them directly

HH-RLHF, WildGuard, and sevdeawesome are all on HuggingFace Hub. Don't upload from local — download on the pod directly:

```bash
# On pod — HuggingFace datasets download automatically on first use
uv run train-pair --output-dir /workspace/pair --epochs 4
# HF downloads datasets to ~/.cache/huggingface/datasets automatically
```

### Code — clone from GitHub (or push a branch first)

```bash
# On pod:
git clone https://github.com/<you>/llm-safety-monitor-training
cd llm-safety-monitor-training && pip install uv && uv sync
```

Or if the repo is private / not pushed yet, use the RunPod web terminal to upload a zip, or `rsync` from local:
```bash
# Local:
rsync -avz --exclude='.venv' --exclude='__pycache__' \
  ~/Documents/muppet-labs/projects/llm-safety-monitor-training/ \
  root@<pod-ip>:/workspace/llm-safety-monitor-training/
```

### Checkpoints — rsync back after training

```bash
# Local — pull checkpoints back after pod finishes:
rsync -avz root@<pod-ip>:/workspace/pair/ \
  ~/Documents/muppet-labs/resources/models/llm-safety-monitor/pair-$(date +%F)/

rsync -avz root@<pod-ip>:/workspace/prompt/ \
  ~/Documents/muppet-labs/resources/models/llm-safety-monitor/prompt-$(date +%F)/

rsync -avz root@<pod-ip>:/workspace/taxonomy/ \
  ~/Documents/muppet-labs/resources/models/llm-safety-monitor/taxonomy-$(date +%F)/
```

Each checkpoint is ~500 MB. With RunPod's egress speeds (~100-300 Mbps), all 3 transfer in ~1-2 min.

### Stop the pod immediately after rsync

```bash
# RunPod web UI → Pod → Stop
# Or via API:
curl -s -X POST "https://api.runpod.io/graphql?api_key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { podStop(input: {podId: \"YOUR_POD_ID\"}) { id } }"}'
```

---

## What NOT to Run on RunPod

| Job | Why not |
|-----|---------|
| error-hide-seek planting / annotation | Claude API — no GPU involved. Runs locally in ~10 min. |
| arxiv corpus fetch | Rate-limited to 0.4s between requests. CPU-bound, I/O-bound. Local is fine. |
| Serving classifiers in production | Hostinger VPS at €5.99/mo vs ~$115/mo for a GPU pod. Not worth it at demo traffic. |
| Running tests / CI | Zero GPU benefit. |

---

## Total Budget Estimate

| Scenario | Jobs | Total GPU time | RunPod cost |
|----------|------|---------------|-------------|
| Minimum (just attack session) | P1 attack run | ~40 min | **~$0.50** |
| Recommended (attack + classifier re-run) | P1 attack + re-train all 3 | ~1.5h across 2 pods | **~$0.75** |
| Extended (scale pair to 376k + attack) | Above + full pair training | ~3.5h across 2 pods | **~$1.50** |
| Exploration (try DeBERTa too) | All above + DeBERTa pair run | ~4h across 3 pods | **~$2.00** |

Well within the $1-2 target for the core jobs.
