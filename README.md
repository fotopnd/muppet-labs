# Anthropic Safeguards Portfolio

Three interconnected systems that together form a complete safety measurement stack: a production safety monitor, an automated red-team evaluation platform, and a randomised controlled trial measuring human uplift from AI-assisted error detection.

---

## System architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                       llm-safety-monitor                            │
│   Kafka ──► pair_classifier ──► Postgres ──► FastAPI ──► Dashboard  │
│                ▲               ▲                                    │
└────────────────┼───────────────┼────────────────────────────────────┘
                 │ [SEP] input   │ source_dataset=red_team
     ┌───────────┴──────┐        │
     │  llm-safety-      │   ┌───┴───────────────────────────────────┐
     │  classifier       │   │         red-team-platform             │
     │  (shared pkg)     │   │   corpus ──► runner ──► outbox ──►    │
     └───────────┬──────┘   │   cluster    ASR/heatmap   Kafka      │
                 │           └───────────────────────────────────────┘
                 │ (same checkpoint, same input format)
     ┌───────────┴─────────────────────────────────────────────────────┐
     │                      error-hide-seek                            │
     │   arXiv corpus ──► plant-errors ──► sessions ──► TPR uplift     │
     │   (Claude red-team)   (3-condition RCT)     (per-category)      │
     └─────────────────────────────────────────────────────────────────┘
```

### How the three components connect

| Link | Description |
|---|---|
| Shared classifier | `llm-safety-classifier` package used by both monitor and red-team. Single `build_input_text(prompt, response)` → `f"{prompt} [SEP] {response}"` ensures both score the same input distribution. |
| Outbox → Kafka | After each attack sweep, `outbox-publisher` delivers run results to the monitor's Kafka topic with `source_dataset=red_team`. Monitor consumers process them identically to live traffic. |
| Disagreements tab | Monitor's Disagreements tab filtered to `source_dataset=red_team` shows which attack types the classifier missed — closing the feedback loop for training data prioritisation. |
| Measurement isolation | error-hide-seek is intentionally decoupled: it uses the Anthropic API for both planting and annotation, giving an independent measure of AI-assisted human uplift. |

---

## Components

| Component | Path | Port | Purpose |
|---|---|---|---|
| `llm-safety-classifier` | `packages/llm-safety-classifier/` | — | Shared inference package: `[SEP]` concatenation, model cache, version |
| `llm-safety-monitor` | `projects/llm-safety-monitor/` | Postgres: 5434 | Streaming classifier, metrics, disagreements, review queue |
| `red-team-platform` | `projects/red-team-platform/` | Postgres: 5433 | Jailbreak corpus, attack runner, ASR measurement, failure clusters |
| `error-hide-seek` | `projects/error-hide-seek/` | Postgres: 5436 | 3-condition RCT, error planting, blue-team annotation, TPR uplift |
| `llm-safety-monitor-training` | `projects/llm-safety-monitor-training/` | — | Training scripts for pair/prompt/taxonomy classifiers |
| Kafka | root `docker-compose.yml` | 9092 | Shared event bus (monitor consumers + red-team outbox publisher) |

---

## Quick start

```bash
# Install all packages (uv workspace — one lock file)
make setup

# Bring up full infrastructure (3 Postgres instances + Kafka)
make infra

# Apply migrations
make migrate

# Run all test suites
make test
```

See `BUILDOUT.md` for the full execution sequence including RunPod GPU setup for the attack sweep.

---

## Component READMEs

- [LLM Safety Monitor](projects/llm-safety-monitor/README.md) — streaming pipeline, calibration, disagreements, escalation router
- [Red-Team Platform](projects/red-team-platform/README.md) — corpus, attack runner, ASR methodology, [SEP] bug history
- [Error Hide and Seek](projects/error-hide-seek/README.md) — RCT design, error taxonomy, scoring logic, telemetry

---

## Port map

| Service | Host port |
|---|---|
| Monitor Postgres | 5434 |
| Red-team Postgres | 5433 |
| Error-hide-seek Postgres | 5436 |
| Kafka | 9092 |
| Zookeeper | 2181 |
