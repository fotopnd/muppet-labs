# Brief Output — system-prompt-injection-detector

**Role:** brief
**Sequence:** `new-project-full` (step 1)
**Date:** 2026-06-06

---

## Project Name

`system-prompt-injection-detector`

---

## Description

A DistilBERT binary classifier and FastAPI middleware service that detects prompt injection attacks in AI agent pipelines, with a proxy endpoint that blocks flagged requests before they reach a downstream LLM, plus a React dashboard showing detection logs and model confidence distributions.

---

## Language(s)

- **Primary:** Python (classifier training + FastAPI service)
- **Frontend:** TypeScript (React SPA)
- **Tooling:** uv, ruff, pnpm, prettier, eslint

Two separate Python projects:
- `injection-detector-training/` — standalone uv project for dataset preparation, synthetic data generation, and HuggingFace Trainer fine-tuning
- `injection-detector/` — FastAPI service with Postgres logging and React dashboard

---

## Success Criteria

The project is done when all of the following are true:

1. **Classifier training** — DistilBERT fine-tuned on SPML-Chatbot Prompt Injection benchmark (HuggingFace: `reshabhs/SPML_Chatbot_Prompt_Injection`) augmented with 5000 synthetic benign examples generated via Ollama (qwen2.5-coder:7b); saves best checkpoint by val F1.
2. **Synthetic data generation** — CLI command `uv run generate-negatives --count 5000` calls Ollama and saves JSONL file; runs independently before training.
3. **Eval metrics** — F1, precision, recall, AUC-ROC, and calibration bins (10 equal-width bins) reported and saved to eval JSON file.
4. **Detection API** — `POST /detect` accepts `{system_prompt, user_message, tool_outputs}`, runs classifier on each field independently, returns per-field probabilities, overall flag, and max probability.
5. **Proxy endpoint** — `POST /proxy` blocks requests where `overall_flagged=True` (returns HTTP 400 with DetectionResponse body) and forwards clean requests to a downstream LLM URL via httpx.
6. **Postgres logging** — every `/detect` call logged to `detection_log` table; threshold configurable via `INJECTION_THRESHOLD=0.7` env var.
7. **Dashboard** — 4-tab React SPA: Detection Log (paginated), Field Analysis (bar chart by field flag rate), Confidence Distribution (histogram of injection probabilities for flagged vs benign), Model Card (eval metrics + calibration chart).
8. **Tests** — pytest for Python (training utilities, API endpoints); vitest for React components.
9. **Runs locally on Apple M4 MPS** — training uses MPS; service runs locally against a Postgres instance on port 5438.

---

## Constraints

- **MPS only for training:** Apple M4 24GB; no CUDA. HuggingFace Trainer with MPS device.
- **Synchronous detection:** no Kafka, no message queue — direct HTTP call to `/detect` per request.
- **Postgres port 5438** (non-default; avoids conflict with other local services).
- **Ollama must be running locally** for synthetic negative generation — documented prerequisite, not an automated fallback.
- **Independent of llm-safety-monitor:** no shared code, no checkpoint dependencies, can be built in parallel.
- **No real-time streaming:** dashboard is polling/query-based, not WebSocket.

---

## Out of Scope

- Multi-label injection classification (binary: injection=1, benign=0 only)
- CUDA / cloud training (MPS local only)
- Kafka or async queuing (synchronous service)
- Fine-tuning beyond DistilBERT (one model; portfolio signal is the full pipeline, not model comparison)
- Model A/B comparison dashboard tab (single model card is sufficient)
- Automated Ollama dataset download (manual prerequisite; CLI assumes Ollama is running)
- Browser extension or SDK wrapper (detection is via HTTP API only)
- Authentication / rate limiting on the detection service (out of scope for v1)

## Open Questions for Planner

1. **Prompt classifier size**: ~6k balanced training examples may be too small for a standalone DistilBERT fine-tune to be credible. Should we augment with additional adversarial prompt datasets (e.g. HarmBench, SALAD-Bench), or accept the small training set with a strong held-out eval narrative?

1. **SPML dataset field names** — assumed to be `prompt` and `label` (or `text` and `label`); implementer must inspect the HuggingFace dataset card to confirm exact column names before writing the data loader.
2. **Synthetic negatives generation** — Ollama prompt template produces plain-text user messages; outputs saved as JSONL with fields `{"text": "...", "label": 0}` matching the injection examples schema.
3. **Label convention** — injection=1, benign=0 (consistent with pair_classifier convention used in other workspace projects).
4. **Threshold default** — `INJECTION_THRESHOLD=0.7` in `.env`; lower values = more sensitive. Trade-off documented in README.
5. **Proxy endpoint** — v1 (not deferred); small addition that provides the key production-realism signal.
6. **Dashboard is a separate React SPA** — not served by FastAPI; same pattern as other workspace projects.
7. **Checkpoint stored at** `resources/models/injection-detector-training/<model-key>-<YYYY-MM-DD>/` per workspace convention.
8. **Eval JSON stored at** `resources/evals/injection-detector-training/<model-key>-<timestamp>.json` per workspace convention.
9. **HuggingFace Trainer** — same training pattern as other projects; warmup_steps (integer) not warmup_ratio; no `no_cuda`; eval_strategy and save_strategy both set to `"epoch"`.
10. **Tool outputs treated as independent fields** — each element of `tool_outputs` list is scored separately; field name in results is `tool_output_0`, `tool_output_1`, etc.

3. **WildGuard for both models**: WildGuard contributes to both the pair classifier and the taxonomy classifier. Does it get split by use (some examples for pair, others for taxonomy), or does it appear in both training sets? Overlap risks data leakage if the eval set is not carefully stratified.

4. **Replay producer mix**: the 60/25/10/5 dataset mix is an assumption. Should the mix be configurable at runtime via the dashboard (a "stream composition" control) or fixed in config? Configurable is more impressive as a demo feature but adds frontend complexity.

5. **`response_text` column**: adding a new column to `classifications` requires a new Alembic migration. Confirm this is the right approach vs storing the response in a separate `interactions` table with a foreign key.

## Handoff

**Next role:** planner

The planner reads this file to define functional requirements, confirm tech stack, map top-level file structure, and list open questions for the architect.

**Flags for planner:**
- Assumption 1 (SPML dataset field names) — planner should note this as an open question for the architect; the implementer must inspect the dataset before writing the data loader.
- Assumption 5 (proxy endpoint in v1) — confirm this is v1 scope; it adds one endpoint and one env var (`DOWNSTREAM_LLM_URL`).
- Assumption 6 (separate React SPA) — confirm dashboard deployment pattern matches other workspace projects.
- Assumption 10 (tool_outputs field naming in detection_log) — confirm JSONB schema can accommodate variable-length tool_outputs list.
