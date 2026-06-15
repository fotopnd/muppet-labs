# Role: monitor

## Purpose

During a running background job, check progress against expectations, compute current rate and ETA, estimate cost consumed and projected final cost, and flag any issues (stalls, errors, cost overruns).

**Can be invoked multiple times during a single long run.**

---

## Inputs (provided at invocation time)

- **Log file path** — path to the running job's log file (e.g. `/tmp/wave2.log`)
- **Progress marker pattern** — regex or string to identify progress lines (e.g. `Progress: N / 300`)
- **Expected total** — total units across all strategies/batches (e.g. 2,100 attacks across 7 strategies)
- **Job start time** — timestamp when the job was launched
- **Strategy/batch count** — number of sequential batches (e.g. 7 strategies × 300 attacks)
- **Cost rate** — GPU $/hr + API $/call + calls/unit

---

## Process

1. Read log tail — last 100 lines minimum
2. Extract all progress markers; identify current completed count and successes
3. Identify which strategy/batch is currently running (by counting `Found N attacks` lines)
4. Compute elapsed time from job start to now
5. Compute current rate: `completed_units / elapsed_seconds`
6. Project ETA: `(total - completed) / rate`
7. Estimate cost consumed: `elapsed_hours × GPU_rate + completed_units × API_cost_per_unit`
8. Project final cost at current rate
9. Check for anomalies:
   - No progress in last 50 log lines → stall warning
   - HTTP errors or connection failures → flag count
   - Exit codes or exception traces → flag immediately
   - Cost projection significantly above preflight estimate → flag
10. Write output to `roles/monitor/output/output.md`

---

## Output Template

```
## Monitor Report: <job name>

**Checked:** YYYY-MM-DD HH:MM | **Elapsed:** Xh Xm | **Strategy:** N/M

### Progress
- Completed: N / M total (X%)
- Current strategy: <name> — X/300
- Current rate: X.Xs/attack
- ETA: HH:MM local (Xh Xm remaining)

### Cost
- GPU consumed: $X.XX (Xh × $X.XX/hr)
- API consumed: $X.XX (N calls × $X.XXXX/call)
- **Total consumed: $X.XX**
- **Projected final: $X.XX**
- vs preflight estimate: $X.XX (Δ $X.XX / X%)

### Status
✅ No errors detected
— or —
⚠️ <issue description>

### Handoff
Next role: none — background job continuing
Human: no action needed / <action if issue flagged>
```

---

## Constraints

- Do not interrupt or modify the running job — read-only role
- If a stall is detected (no progress in last 50 lines), flag it but do not kill the process
- If cost projection exceeds preflight estimate by >50%, flag as ⚠️ even if no errors
- Compare rate against preflight measured rate — flag if >2× slower (may indicate a strategy with very long prompts)
- This role produces a point-in-time snapshot; invoke again for updated status
