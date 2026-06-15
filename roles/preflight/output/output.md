# Preflight Report: Wave 3b — llama3.1:8b

**Sample:** 2 local Ollama calls | **Population:** 3,900 attacks (13 strategies × 300) | **Date:** 2026-06-14

> ⚠️ **Methodology note:** Attack runner has no `--dry-run --limit`. Local measurements use direct Ollama calls. RunPod projection uses two cases: (1) Wave 3a empirical rate (optimistic — same GPU, similar model size) and (2) 1.5× Wave 3a rate (conservative — llama3.1:8b is 1.8× slower than qwen2.5:7b by local tok/s; RunPod fixed overhead shrinks this ratio, so 1.5× is the midpoint estimate). Haiku cost from Wave 3a measured actuals.

---

### Measured (2 local calls, llama3.1:8b on M4)

- **tok/s local:** 10.8 (vs qwen2.5:7b 19.5 — llama3.1:8b ~1.8× slower locally)
- **Wall time/call local:** 5.19s avg (sample 1: 7.94s / sample 2: 2.44s)
- **Output tokens/call:** ~56 avg (85 / 27) — variable due to compliance rate
- **Input tokens/call:** 55 avg
- **Haiku cost/call:** ~$0.000430 (Wave 3a measured actuals)

---

### Projected (full population — RunPod RTX 5090)

| Case | Rate | Wall time (raw) | Buffered (+20%) | GPU cost | API cost | Total |
|------|------|-----------------|-----------------|----------|----------|-------|
| Optimistic (Wave 3a parity) | 2.59s/atk | 2.8h | 3.4h | $3.33 | $1.68 | **$5.01** |
| **Conservative (1.5× Wave 3a)** | **3.9s/atk** | **4.2h** | **5.1h** | **$5.02** | **$1.68** | **$6.70** |

**Use conservative estimate for planning: ~$6.70, ~5h wall time.**

---

### Local vs RunPod

| Option | Wall time | GPU cost | API cost | Total | Notes |
|--------|-----------|----------|----------|-------|-------|
| Local (M4) | ~6.3h | free | $1.68 | $1.68 | Ties up machine; above 3h threshold |
| RunPod 3090 | ~5–7h | $2.30–3.22 | $1.68 | $3.98–4.90 | Slower than 5090 |
| RunPod 4090 | ~4–5h | $2.76–3.45 | $1.68 | $4.44–5.13 | |
| **RunPod 5090** | **~3–5h** | **$3.33–5.02** | **$1.68** | **$5.01–6.70** | Fastest; cheapest at optimistic rate |

**Platform recommendation: RUNPOD 5090**
Local 6.3h >> 3h threshold → RunPod. 5090 gives fastest wall time; pod is already stopped with qwen2.5:7b cached — llama3.1:8b needs to be pulled (~4.7 GB, ~2 min).

---

### Anomalies / Risks

- llama3.1:8b local tok/s (10.8) is ~45% of qwen2.5:7b (19.5). If this ratio holds exactly on RunPod, rate would be ~4.7s/attack and total ~5.0h GPU/$6.61 total. Conservative 1.5× estimate is more likely than exact 1.8× on RunPod due to fixed overhead.
- Wave 3a ran 2h 48m vs preflight estimate of 1.6h — preflight underestimated. For Wave 3b, conservative estimate used upfront.
- combination_1 and base64 had 294/297 attacks in Wave 3a (not 300) — minor drop rate, budget impact minimal.

---

### Go/No-Go

**GO**

Estimated cost ($5–7 range) is within budget. Wall time 3–5h is a single RunPod session. No blockers.

**Confirm Anthropic credit balance covers ~$1.68 API cost before launching.**

---

### Handoff

Next role: none — human decision point
Human: confirm credit balance, spin up RunPod pod (Resume stopped pod or new), pull `llama3.1:8b`, update `.env` OLLAMA_BASE_URL + OLLAMA_MODEL, approve launch of Wave 3b
