# Brief Output — multi-turn-safety-monitor

**Role:** brief
**Sequence:** `new-project-full` (step 1)
**Date:** 2026-06-06

---

## Project Name

`multi-turn-safety-monitor`

---

## Description

A conversation-level safety evaluation system that tracks per-turn toxicity scores across multi-turn dialogue and detects adversarial escalation patterns — foot-in-door, persona hijack, context reset, incremental harm — that stateless single-turn classifiers miss.

---

## Language(s)

- **Backend:** Python 3.12 (uv, FastAPI, SQLAlchemy async, Pydantic v2, HuggingFace transformers)
- **Frontend:** TypeScript (React 18, TanStack Query, recharts, shadcn/ui, Vite, pnpm, vitest)
- **Database:** PostgreSQL 16 (port 5437)
- **Tooling:** ruff (Python), prettier + eslint (TypeScript)

---

## Success Criteria

The project is done when all of the following are true:

1. **Conversation ingestion** — `POST /conversations` accepts `{system_prompt: str, turns: list[{role: user|assistant, content: str}]}` and persists the conversation and all turns to Postgres. Returns `ConversationDetail` with `id` and initial status `pending`.
2. **Per-turn scoring** — Each user turn is scored independently via the shared DistilBERT fine-tuned checkpoint at `resources/models/toxicity-classifier-finetuned/distilbert-best`. Scores are stored on the `turns` table. Assistant turns are not scored (no ground truth for assistant outputs).
3. **Escalation detection** — `analyzer.py` computes an `escalation_score` (weighted combination of max turn score, mean turn score, and linear slope across user-turn score sequence), assigns `status` (clean/flagged/escalating), and persists a `ConversationAnalysis` record.
4. **Pattern classification** — Escalating conversations are labelled with one of five patterns: `foot_in_door`, `persona_hijack`, `context_reset`, `goal_hijack`, `incremental_harm`. Pattern rules are deterministic (keyword + score-shape rules), not a secondary model.
5. **REST API** — GET /conversations (paginated, filterable by status and pattern), GET /conversations/{id} (full detail with turns and analysis), POST /conversations/{id}/reanalyze (re-score and re-analyse), GET /metrics (aggregate stats).
6. **Seed script** — `uv run seed` loads 20 synthetic conversations from a JSON fixture file in `tests/fixtures/`: 10 clean, 5 flagged (single high-score turn), 5 escalating (rising turn scores with a recognisable pattern label).
7. **Dashboard** — 4-tab React SPA: Overview (metrics cards + recent flagged list), Conversation Queue (filterable table), Conversation Explorer (turn timeline LineChart + colour-coded transcript + analysis panel), Pattern Analytics (pattern breakdown PieChart + escalation score histogram).
8. **Tests** — pytest integration tests (ingest, list filters, detail, metrics endpoint with seeded data); unit tests for escalation_score computation, slope calculation, pattern classification. Vitest component tests (ConversationTable, TurnTimeline, PatternPie, MetricsCards).

---

## Constraints

- **MPS only** — classifier inference runs on Apple M4 24GB. No CUDA. HuggingFace `pipeline` auto-selects MPS.
- **Shared checkpoint** — uses `resources/models/toxicity-classifier-finetuned/distilbert-best`. No new training run; this project consumes the existing fine-tuned model.
- **Synchronous scoring** — turn scoring happens inline during `POST /conversations` (no background queue). Max expected conversation length is 20 turns; latency budget is acceptable for a demo.
- **Postgres port 5437** — avoids conflict with case-queue (5432), moderation-stream (5433), red-team-platform (5435), cai-preference-trainer (5436).
- **No auth** — single-user local tool; no session or token management.
- **No streaming** — dashboard is polling/query-based (TanStack Query with refetch interval), not WebSocket.

---

## Out of Scope

- Secondary ML model for pattern classification (rule-based only; saves training cost and is interpretable)
- Scoring assistant turns (no ground truth; user turns are the attack vector)
- Real-time streaming ingestion (Kafka, webhooks) — synchronous HTTP ingestion only
- Multi-user access control or annotator identity
- Conversation export or download
- Fine-tuning a new model on multi-turn data (this is a consumption project, not a training project)
- Integration with llm-safety-monitor or case-queue APIs (standalone service)

---

## Assumptions

1. The shared DistilBERT checkpoint at `resources/models/toxicity-classifier-finetuned/distilbert-best` is compatible with `AutoModelForSequenceClassification.from_pretrained()` — confirmed from prior training project.
2. Binary toxicity score (float 0–1) is sufficient signal for escalation detection; no multi-label output needed.
3. Pattern taxonomy is fixed at five categories for v1; a JSON config for pattern rules is a v2 concern.
4. Postgres runs in Docker Compose (same pattern as other workspace projects); the dashboard connects to the API, not directly to Postgres.

---

## Handoff

**Next role:** planner

The planner reads this file to define functional requirements, confirm the technology stack, map top-level file and module structure, and raise open questions for the architect.

**Flags for planner:**
- Assumption 3 (fixed pattern taxonomy) — planner should decide whether the pattern rules live as Python constants or as a YAML/JSON config that can be edited without a code change.
- Constraint on synchronous scoring — planner should confirm this is acceptable or flag if the conversation fixture size makes latency a concern.
- File structure decision: separate `multi-turn-safety-monitor-api/` + `multi-turn-safety-monitor-ui/` directories, or a single `projects/multi-turn-safety-monitor/` root with `api/`, `web/`, `tests/` subdirectories (matching cai-preference-trainer pattern).
