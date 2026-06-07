# Red-Team Platform — Attack Session Plan

**Target model:** gemma2:9b  
**Corpus:** sevdeawesome/jailbreak_success (35 strategies × 300 harm goals)  
**Scope:** 10 priority strategies × 300 goals = 3,000 attacks  
**Est. wall clock:** ~4-5h local (M4 overnight) or ~1.5h on RunPod 4090 (~$1.50)

---

## Pre-flight

```bash
# 1. Bring down llm-safety-monitor (shares port 5435)
cd ~/Documents/muppet-labs/projects/llm-safety-monitor && docker compose down

# 2. Start red-team infra
cd ~/Documents/muppet-labs/projects/red-team-platform
docker compose up -d
uv run alembic upgrade head

# 3. Seed corpus (~4 min)
uv run seed-corpus

# 4. Verify exact strategy strings in DB after seed
docker exec -it $(docker ps -qf name=redteam) psql -U redteam redteam \
  -c "SELECT strategy, count(*) FROM attacks GROUP BY strategy ORDER BY count DESC;"

# 5. Start API + frontend (two terminals)
uv run api
cd web && pnpm dev      # will start on 5173 or next available port
```

---

## Wave sequence — Phase 1 (priority, run these first)

Check StrategyComparison and CoverageHeatmap in the frontend after each wave.

| Wave | Strategy | Expected ASR | Rationale |
|---|---|---|---|
| 1 | `DAN` | High | Baseline — validates full pipeline end-to-end |
| 2 | `evil_system_prompt` | High | System prompt override — hard for any model to resist |
| 3 | `refusal_suppression` | Medium-high | Directly targets safety refusal behaviour |
| 4 | `combination_1` | High | Multi-technique — usually highest ASR overall |
| 5 | `few_shot_json` | Medium | Structured injection — model-dependent variation |
| 6 | `AIM` | Medium | Roleplay persona attack — good contrast with encoding attacks |

```bash
for strategy in DAN evil_system_prompt refusal_suppression combination_1 few_shot_json AIM; do
    echo "=== Wave: $strategy ===" && uv run attack --strategy "$strategy"
done
```

After Phase 1 (~2-3h): run cluster to see emerging failure patterns.

```bash
uv run cluster
```

---

## Wave sequence — Phase 2 (overnight sweep)

Adds encoding/obfuscation and multi-shot strategies for full coverage of the strategy space.

```bash
caffeinate -i bash -c '
  for strategy in autodan prefix_injection multi_shot_25 base64; do
    echo "=== Wave: $strategy ===" && uv run attack --strategy "$strategy"
  done
'
```

| Strategy | Expected ASR | Rationale |
|---|---|---|
| `autodan` | Medium | Automated adversarial — tests model robustness to novel phrasing |
| `prefix_injection` | Medium | Prompt injection via prefix — clean contrast with suffix attacks |
| `multi_shot_25` | Medium | 25-shot context override — tests in-context learning exploitation |
| `base64` | Low-medium | Encoding evasion — tests whether Gemma decodes and complies |

---

## RunPod option (instead of local overnight)

**Setup (~20-30 min, one-time):**

1. Create account at runpod.io
2. Deploy a GPU pod with the **Ollama** community template
   - GPU: RTX 4090 (24GB, ~$0.74/hr) — sufficient for gemma2:9b
   - Expose port 11434
3. SSH into the pod and pull the model:
   ```bash
   ollama pull gemma2:9b
   ```
4. Get the pod's public URL for port 11434 (shown in RunPod dashboard)
5. Update `.env` in red-team-platform:
   ```
   OLLAMA_BASE_URL=https://<pod-id>-11434.proxy.runpod.net
   ```
6. Run attack waves locally — Ollama calls go to RunPod, pair_classifier stays on M4

**Cost:**
- 10 strategies (3,000 attacks): ~1.5h → **~$1.10**
- Full 35 strategies (10,800 attacks): ~4h → **~$3.00**
- Shut down pod immediately after — no idle charges

**When done:** restore `.env` OLLAMA_BASE_URL to `http://localhost:11434`.

---

## Post-sweep — analysis steps

```bash
# 1. Re-cluster with full dataset
uv run cluster

# 2. Open frontend
cd web && pnpm dev
```

Review in this order:

1. **StrategyComparison** — bar chart sorted by ASR. Top bar = most dangerous strategy against gemma2:9b.
2. **CoverageHeatmap** — 13 harm categories × 10 strategies. High-ASR cells are the finding.
3. **FailureClusters** — qualitative themes: what do successful jailbreaks look like? Common patterns?
4. **SampleReview** — read 5-10 actual jailbreak responses. Useful quotes for the writeup.

---

## Filling in benchmarks/results.md

After reviewing the dashboard, fill in:

```markdown
## Session 1 — gemma2:9b, <date>

**Corpus:** sevdeawesome/jailbreak_success  
**Strategies run:** 10 of 35  
**Total attacks:** ~3,000  
**Overall ASR:** X.X%

### Top strategies by ASR
1. strategy_name — XX%
2. strategy_name — XX%
3. strategy_name — XX%

### Most vulnerable harm categories
1. category_name — XX% avg ASR across strategies
2. category_name — XX%
3. category_name — XX%

### Key finding
[1-2 sentence narrative: which strategy class (roleplay / encoding / multi-shot) was most
effective, and which harm categories were least protected.]

### Cluster themes
- Cluster N (size X): [theme — e.g. "roleplay persona + authority figure"]
- Cluster N (size X): [theme]
```

---

## Notes

- **Strategy strings:** verify exact names from the seed DB query before running waves. Names in sevdeawesome may differ from the list above (e.g. `combination_1` might be `combination-1`).
- **Timeout:** `OLLAMA_TIMEOUT_S=120` in `.env`. If gemma2:9b is slow on long prompts, increase to 180.
- **Pair classifier confidence:** threshold is 0.5. Borderline responses (0.45-0.55 confidence) are coin-flip calls — expected given the pair classifier's bimodal behaviour (F1=0.549, recall=0.91).
- **Port conflict reminder:** llm-safety-monitor and red-team-platform both use port 5435. Only one can run at a time.
