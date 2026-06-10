# RunPod — M4 Offload Strategy

**Philosophy:** Use RunPod for any job that would tie up the M4 for more than ~1h. Target: spend $1-2 in credits, offload 4-10h of local compute, get results back in under 1h.

RunPod is for **training runs and batch simulation jobs only.** Production deployment stays on Hostinger VPS.

**Prices last verified: 2026-06-09 (Community Cloud spot).** A10G and A100 40GB not found in search — marked *(unverified)*; check console before running.

---

## Current Jobs to Offload

| Job | M4 time (actual/est) | RunPod GPU | RunPod time | Cost | Priority |
|-----|---------------------|-----------|-------------|------|----------|
| red-team attack session (1,800 attacks, 6 strategies, gemma2:9b) | ~4-5h | RTX 4090 spot | **~4h actual** | **~$1.35 actual** | **P1 complete** |
| Re-train all 3 RoBERTa classifiers (4 epochs each) | ~4.5h (actual) | A10G spot *(unverified)* | ~55 min + 15 min overhead | ~$0.41–$0.70 | If re-run needed |
| **Total (attack done, retrain pending)** | | | | **~$1.35–$2.05** | |

> **Post-mortem:** Attack session ran 6× over original $0.23 estimate. See Calibration Protocol below.

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
| RTX 3090 | ~75 | ~30 min | ~50 min | ~$0.19 ✓ | ~$0.16 |
| **RTX 4090** | **~110** | **~25 min** | **~40 min** | **~$0.34 ✓** | **~$0.23** |
| A10G | ~80 | ~28 min | ~47 min | ~$0.45 *(unverified)* | ~$0.35 |

**Pick: RTX 4090 spot.** See `resources/runpod-plan.md` for full setup.

> **These token-throughput estimates are optimistic.** Phase 1 actual was ~4h for 1,800 attacks (~8s/atk avg). See Measured Rates below.

#### Measured s/attack — Phase 1 sweep (gemma2:9b, RTX 4090, 2026-06-09)

Time is driven by **response length, not prompt length.** Refusal responses (~50 tokens) are faster than successful jailbreak responses (~200-400 tokens). Network retry spikes add 1.3-2.5× wall clock overhead.

| Strategy | Prompt chars | Nominal s/atk | Wall clock s/atk | 300 atk wall time | Notes |
|----------|-------------|---------------|-----------------|-------------------|-------|
| gcg | 197 | 3.1s | 3.0s | **15 min** | Minimal retries |
| evil_system_prompt | 79 | 3.5s | 5.0s | **25 min** | Some retry spikes |
| refusal_suppression | 709 | 1.9s | 4.5s | **22 min** | Fast (refusals short); retry spikes |
| combination_1 | 513 | 2.4s | 6.3s | **31 min** | Retry spikes |
| few_shot_json | 6,768 | ~9.2s | ~21.8s | **~109 min** | Long context = slow prefill; many retries |
| AIM | 1,788 | ~5-7s (est) | ~10-15s (est) | **~50-75 min (est)** | Not yet complete |
| **Phase 1 total** | | | | **~4h actual** | vs 40 min estimated |

**Rule of thumb for future sweeps:** 300 attacks × (nominal_rate × 1.4 retry buffer) / 60 = wall minutes. For a 6-strategy Phase 1 mix like above, budget **~3-4 hours** on RTX 4090.

**Calibrate before committing:** Run 20 attacks per new strategy and measure actual s/atk before estimating the full sweep.

---

### For RoBERTa-base training (125M params, batch=32, max_len=128)

M4 MPS baseline: **1.35-1.46 s/step**. CUDA speedup over MPS for this model: 5-8×.

**Steps:** 50k train samples / batch 32 × 4 epochs = 6,250 steps.

| GPU | VRAM | Step time (est) | Pair (50k, 4ep) | Prompt (4ep) | Taxonomy (4ep) | Training only | Pod overhead | Total billed | Spot $/hr | Cost |
|-----|------|----------------|----------------|-------------|---------------|--------------|-------------|-------------|-----------|------|
| T4 | 16 GB | ~0.45s | ~38 min | ~10 min | ~10 min | ~58 min | +15 min | **~73 min** | ~$0.16 | **~$0.19** |
| **A10G** | **24 GB** | **~0.25s** | **~21 min** | **~6 min** | **~6 min** | **~33 min** | +15 min | **~48 min** | **~$0.45 *(unverified)*** | **~$0.36** |
| A100 40GB | 40 GB | ~0.12s | ~10 min | ~3 min | ~3 min | ~16 min | +15 min | **~31 min** | ~$1.24 *(unverified)* | **~$0.64** |

**Overhead breakdown (always add to estimate):**
- Pod startup + uv sync: ~3-5 min
- HF dataset download (HH-RLHF + WildGuard, first run): ~8-12 min
- Total: **+15 min fixed** to any training estimate

**Pick: A10G spot.** T4 is the budget pick but tighter on VRAM. A10G comfortable at ~$0.36 with overhead. **Verify A10G price in console before booking** — unverified.

**Calibrate before full run:** `uv run train --model pair --max-train-samples 3200 --epochs 1` runs ~100 steps. Measure step time, extrapolate. If A10G step time ≠ 0.25s, adjust total before committing.

---

### For DeBERTa-v3-base or ModernBERT (if you want to try larger models)

DeBERTa-v3-base: 184M params. ModernBERT-base: 149M params.

| GPU | DeBERTa step time | Pair training only | Pod overhead | Total billed | Spot $/hr | Cost |
|-----|------------------|-------------------|-------------|-------------|-----------|------|
| A10G | ~0.6s | ~55 min | +15 min | **~70 min** | ~$0.45 *(unverified)* | **~$0.53** |
| A100 40GB | ~0.25s | ~23 min | +15 min | **~38 min** | ~$1.24 *(unverified)* | **~$0.79** |
| **A100 80GB** | **~0.18s** | **~17 min** | +15 min | **~32 min** | **~$0.89 ✓** | **~$0.47** |

**Pick: A100 80GB spot** for DeBERTa. At $0.89/hr (verified), it's still the best value — ~$0.47 total with overhead.

**Step time is theoretical** (derived from param-count scaling from M4 baseline). Calibrate with 100-step warmup before committing: any A100 80GB pod, `uv run train --model pair --max-train-samples 3200 --epochs 1`, measure and extrapolate.

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

## Total Budget Estimate (revised)

| Scenario | Jobs | Total GPU time | RunPod cost |
|----------|------|---------------|-------------|
| ~~Minimum (attack only)~~ | ~~P1 attack~~ | ~~40 min~~ | ~~$0.23~~ |
| **P1 attack (actual)** | **6 strategies × 300 attacks** | **~4h** | **~$1.35** |
| Retrain all 3 RoBERTa | A10G (with 15 min overhead) | ~48 min | **~$0.36** |
| Extended (scale pair to 376k) | A10G, ~2.2h training + 15 min | ~2.6h | **~$1.18** |
| DeBERTa pair run | A100 80GB (with overhead) | ~32 min | **~$0.47** |
| **Full portfolio (P1 done + retrain + DeBERTa)** | | | **~$2.18** |

Attack run alone exceeded the original $1-2 total budget. Training jobs remain within target. A10G price unverified — check console before running.

---

## Calibration Protocol

**Rule: measure before you commit on anything > $0.20.**

### Inference sweeps (attack runner)

```bash
# 1. Run 20 attacks per new strategy and measure
time attack --strategy <name> --limit 20

# 2. Compute wall s/atk, apply to full run
python3 -c "
s_per_atk = MEASURED_SECS / 20
n = 300
buffer = 1.4  # retry overhead
hr = 0.34     # RTX 4090 rate
print(f'{s_per_atk * n * buffer / 60:.0f} min, ${s_per_atk * n * buffer / 3600 * hr:.2f}')
"
```

Key drivers:
- Short prompts (< 500 chars): 1.9-3.5s/atk nominal — response length dominates
- Long prompts (> 5k chars): 8-10s/atk nominal — prefill time dominates
- Add 1.3-2.5× for ReadError retry overhead on RunPod proxy

### Training jobs

```bash
# 1. Run 100-step calibration before full training
uv run train --model pair --max-train-samples 3200 --epochs 1
# (3200 samples / batch 32 = 100 steps)

# 2. Time the 100 steps, project to full run
python3 -c "
step_time = MEASURED_100_STEP_SECS / 100
total_steps = 6250  # 50k / 32 * 4 epochs
overhead_min = 15   # pod setup + HF download
rate = 0.45         # A10G (verify!)
total_min = total_steps * step_time / 60 + overhead_min
print(f'{total_min:.0f} min, \${total_min / 60 * rate:.2f}')
"
```

Always add **15 min fixed overhead** for pod startup + HF dataset download on first run.
Step time estimates are theoretical — calibrate on actual hardware before committing to multi-hour runs.
