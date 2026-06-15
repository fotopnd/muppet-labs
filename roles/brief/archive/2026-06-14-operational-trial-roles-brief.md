# Brief: Operational Trial Roles

**Date:** 2026-06-14  
**Author:** brief role  
**Routing:** brief → planner → implementer (new roles, Markdown-only deliverables)

---

## Problem

When running expensive API or GPU jobs — haiku judge batches, Ollama inference sweeps, RunPod attack sessions — we have consistently produced inaccurate cost and time estimates:

| Incident | Estimated | Actual |
|---|---|---|
| Wave 1 reclassify dry run | sample only | consumed full 10,800 haiku calls (no --limit) |
| Wave 2 wall time (local M4) | 2.5h | ~10h |
| Wave 2 wall time (RunPod) | 2.9h | ~1.7h |
| Wave 2 GPU cost | $2.87 | ~$1.68 |

Root causes:
1. No --limit on dry runs → full population consumed
2. No measurement step between dry run and full launch → estimates based on assumptions, not observations
3. No live visibility during long runs → can't detect stalls, cost overruns, or errors early

---

## Proposed Roles

Two new generic workspace roles: **preflight** and **monitor**. Both are Markdown-only deliverables (no code). Both are generic — no project-specific logic baked in.

---

### Role: preflight

**Purpose:** Run a small sample of any expensive job, measure actual performance, project to full population, and produce a go/no-go recommendation before committing to a full wave.

**When to invoke:** Before any job that calls paid APIs or GPU inference at scale. Mandatory for any job estimated >$1 or >1h.

**Inputs (provided at invocation time):**
- Command to test (with `--dry-run --limit N` or equivalent)
- Sample size N (default: 10)
- Full population size
- Cost drivers: API type + model (e.g. haiku at $0.80/MTok in, $4.00/MTok out), GPU type + rate (e.g. RTX 5090 at $0.99/hr)
- Prompt structure (to estimate token counts if not in logs)
- Local hardware throughput (e.g. M4 at 16.2 tok/s for gemma2:9b — from measured rates in `resources/runpod-pricing.md`)

**Process:**
1. Run the command with `--dry-run --limit N`
2. Parse logs: extract wall time per call, any token counts reported
3. If token counts not in logs: estimate from prompt structure (input chars ÷ 4 ≈ tokens) and flag as estimated
4. Compute per-call metrics: s/call, tokens in, tokens out, API cost/call
5. Project to full population: total time, total API cost, total GPU cost, combined total
6. Check for anomalies: errors, unexpected output format, rate limits, stalled calls
7. Write output report

**Output (preflight/output/output.md):**
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
| Option | Wall time | GPU cost | API cost | Total | Notes |
|--------|-----------|----------|----------|-------|-------|
| Local (M4) | Xh | free | $X.XX | $X.XX | requires AC + caffeinate |
| RunPod 3090 | Xh | $X.XX | $X.XX | $X.XX | |
| RunPod 4090 | Xh | $X.XX | $X.XX | $X.XX | |
| RunPod 5090 | Xh | $X.XX | $X.XX | $X.XX | |

**Platform recommendation: LOCAL / RUNPOD \<GPU\>**
<one sentence rationale — time saved, cost delta, any constraints e.g. travel>

Decision rules applied:
- Local < 1h → local
- Local 1–3h → borderline, flag AC + caffeinate requirement
- Local > 3h → RunPod (cheapest GPU by total cost)
- Any run on battery or during travel → RunPod regardless

### Anomalies
- <list any errors, unexpected formats, slow calls>

### Go/No-Go
GO / NO-GO / INVESTIGATE
<one sentence rationale>

### Handoff
Next role: (none — human decision point)
Human: approve launch on recommended platform, or override with alternative
```

---

### Role: monitor

**Purpose:** During a running background job, check progress, compute rate and ETA, estimate cost consumed and projected, and flag any issues.

**When to invoke:** After launching a background wave or sweep. Can be invoked multiple times during a long run.

**Inputs (provided at invocation time):**
- Log file path
- Progress marker pattern (e.g. `Progress: N / 300`)
- Expected total (e.g. 2,100 attacks across 7 strategies)
- Job start time
- Cost rate: GPU $/hr + API $/call + calls/attack

**Process:**
1. Read log tail for progress markers
2. Compute completed count, elapsed time, rate (units/second)
3. Project ETA and remaining time
4. Estimate cost consumed (elapsed GPU time × rate + completed calls × cost/call)
5. Project final cost at current rate
6. Check for errors, stalls (no progress in last N lines), connection failures
7. Write status report

**Output (monitor/output/output.md):**
```
## Monitor Report: <job name>

**Checked:** YYYY-MM-DD HH:MM | **Elapsed:** Xh Xm

### Progress
- Completed: N / M (X%)
- Current rate: X.Xs/attack
- ETA: HH:MM (Xh Xm remaining)

### Cost
- GPU consumed: $X.XX (Xh × $X.XX/hr)
- API consumed: $X.XX (N calls × $X.XXXX/call)
- **Total consumed: $X.XX**
- Projected final: $X.XX

### Status
✅ No errors detected / ⚠️ <issue>

### Handoff
Next role: (none — background job continuing)
Human: no action needed / <action required>
```

---

## Implementation Notes

- Both roles are **Markdown-only** — no code, no scripts
- Both roles are **generic** — inputs parameterise the job; no project-specific logic in the role contract
- preflight replaces the informal "dry run and eyeball" pattern that caused the credit burn incident
- monitor replaces manual `tail -f` + mental arithmetic during long runs
- Both roles should be added to `resources/routing.md` as standalone single-role sequences (they don't chain into planner/architect/implementer)
- Role directories: `roles/preflight/` and `roles/monitor/`

---

## Routing Addition (for routing.md)

```
## pre-wave-check
Purpose: Validate cost and time before launching any expensive API/GPU job.
Roles: preflight
Trigger: Any job estimated >$1 or >1h wall time.

## in-flight-check  
Purpose: Progress and cost visibility during a running background job.
Roles: monitor
Trigger: Any time during a long background job.
```

---

## Handoff

**Next role:** planner  
**Human:** Review proposed role contracts above. If approved, invoke planner to produce implementation plan for `roles/preflight/CONTEXT.md` and `roles/monitor/CONTEXT.md`, and update `resources/routing.md` with the two new sequences.
