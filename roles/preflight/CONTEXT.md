# Role: preflight

## Purpose

Run a small sample of any expensive API or GPU job, measure actual performance metrics, project to full population, and produce a go/no-go recommendation with a local vs RunPod platform decision before committing to a full wave.

**Mandatory for any job estimated >$1 or >1h wall time.**

---

## Inputs (provided at invocation time)

- **Command** — the script/command to test, with `--dry-run --limit N` or equivalent
- **Sample size N** — number of calls to measure (default: 10, minimum: 5)
- **Full population size** — total calls in the full run
- **API cost drivers** — model name + input $/MTok + output $/MTok (e.g. haiku: $0.80 in / $4.00 out)
- **GPU cost driver** — GPU type + spot $/hr (from `resources/runpod-pricing.md`)
- **Prompt structure** — approximate input token count per call (to estimate if logs don't report tokens)
- **Local hardware throughput** — measured tok/s for the model on M4 (from `resources/runpod-pricing.md`)

---

## Process

1. Run `--dry-run --limit N` (never omit `--limit` — see [[feedback-dry-run-limits]])
2. Parse logs: extract wall time per call (min, max, mean), token counts if logged
3. If token counts not in logs: estimate from prompt structure (`input_chars ÷ 4 ≈ tokens`); flag as estimated
4. Compute per-call metrics: s/call, tokens in, tokens out, API cost/call
5. Project to full population: total time, total API cost, total GPU cost, combined total
6. Run local vs RunPod comparison using `resources/runpod-pricing.md` measured rates and current prices:
   - Compute local wall time: `population × measured_s_per_call`
   - Compute RunPod wall time per GPU: `local_time × (local_tok_s / runpod_tok_s)`
   - Compute RunPod total cost: `GPU_hours × rate + API_cost`
   - Apply decision rules (see output template)
7. Check for anomalies: errors, non-numeric output, rate limits, stalled calls, unexpected response format
8. Write output to `roles/preflight/output/output.md`

---

## Output Template

```
## Preflight Report: <job name>

**Sample:** N calls | **Population:** M calls | **Date:** YYYY-MM-DD

### Measured (from N-call sample)
- Wall time/call: Xs (min Xs, max Xs)
- Tokens in/call: ~N (estimated / measured)
- Tokens out/call: ~N (estimated / measured)
- API cost/call: $X.XXXX

### Projected (full population)
- Wall time: Xh Xm
- API cost: $X.XX
- GPU cost: $X.XX (Xh × $X.XX/hr)
- **Total: $X.XX**

### Local vs RunPod
| Option       | Wall time | GPU cost | API cost | Total  | Notes                      |
|--------------|-----------|----------|----------|--------|----------------------------|
| Local (M4)   | Xh Xm     | free     | $X.XX    | $X.XX  | requires AC + caffeinate   |
| RunPod 3090  | Xh Xm     | $X.XX    | $X.XX    | $X.XX  |                            |
| RunPod 4090  | Xh Xm     | $X.XX    | $X.XX    | $X.XX  |                            |
| RunPod 5090  | Xh Xm     | $X.XX    | $X.XX    | $X.XX  |                            |

**Platform recommendation: LOCAL / RUNPOD <GPU>**
<one sentence rationale — time saved, cost delta, any constraints>

Decision rules applied:
- Local < 1h → local
- Local 1–3h → borderline; flag AC + caffeinate requirement
- Local > 3h → RunPod (cheapest GPU by total cost from runpod-pricing.md)
- Battery or travel → RunPod regardless of time

### Anomalies
- <none / list issues>

### Go/No-Go
**GO / NO-GO / INVESTIGATE**
<one sentence rationale>

### Handoff
Next role: none — human decision point
Human: approve launch on recommended platform, or override with alternative
```

---

## Constraints

- Never run without `--limit` — see [[feedback-dry-run-limits]]
- Always pull GPU prices from `resources/runpod-pricing.md` — do not use cached assumptions
- Flag all token count estimates clearly as `(estimated)` vs `(measured)`
- If the sample produces errors on >20% of calls: verdict is INVESTIGATE, not GO
- This role does not launch the full run — it only produces the report
