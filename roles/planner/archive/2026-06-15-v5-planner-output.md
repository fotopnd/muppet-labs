# Planner Output — Llama Guard Baseline Comparison

**Role:** planner  
**Sequence:** add-feature  
**Date:** 2026-06-13  
**Reads:** `roles/brief/archive/2026-06-12-llm-guard-baseline-brief.md`

---

## Project

`llm-guard-baseline` — a standalone eval script that benchmarks Llama Guard 3 (via Ollama) against the trained pair classifier on the same WildGuard held-out test split, producing a side-by-side F1/precision/recall/latency table written to `benchmarks/baseline-comparison.md`.

---

## Open Questions Resolved (from brief handoff)

**Q1 — Is the WildGuard test split saved to disk?**  
No. The eval JSON at `resources/evals/llm-safety-monitor/pair-20260607T142119.json` stores only aggregate metrics (`f1`, `precision`, `recall`, `sample_count=6337`) — no `test_texts` or `test_labels` keys. However, `split_wildguard(seed=42)` is fully deterministic (fixed RNG seed, public HuggingFace dataset). Calling it in the compare-baselines script regenerates the identical held-out split at runtime. No disk save needed; no `--save-test-split` flag required.

**Q2 — Is llama-guard3 pullable via Ollama on M4?**  
Yes — it's an official Ollama model. Currently NOT pulled: `ollama list` shows only `qwen2.5-coder:7b` and `gemma2:9b`. The script must check for presence and fail fast with a clear message: `"Run: ollama pull llama-guard3"`. Pull is a prerequisite step, not part of the script.

**Q3 — What input format does Llama Guard 3 expect?**  
Llama Guard 3 evaluates conversations. Via Ollama's OpenAI-compatible chat API, it applies its template automatically. The WildGuard pair eval texts use `"{prompt} [SEP] {response}"` format — split on `" [SEP] "` to recover prompt and response, then pass as `[{"role": "user", "content": prompt}, {"role": "assistant", "content": response}]`. Parse the output: `1 (unsafe) if response.strip().lower().startswith("unsafe") else 0 (safe)`.

**Q4 — Which eval subset to use for the pair classifier comparison row?**  
Use WildGuard `pair_eval_texts`/`pair_eval_labels` only (not the HH-RLHF test mix used in the stored JSON). Rationale: Llama Guard 3 is not trained on HH-RLHF, so including it would disadvantage the baseline unfairly. Same WildGuard-only subset applies to all three models in the table. The pair classifier result will differ slightly from the stored JSON (6337 → ~2300 samples) — note this in the output table.

---

## Requirements

1. `uv run compare-baselines` runs from `projects/llm-safety-monitor-training/` without arguments
2. Script loads `split_wildguard(seed=42).pair_eval_texts` and `pair_eval_labels` at runtime — no pre-saved test file needed
3. Script checks for `llama-guard3` in Ollama before running; exits with a clear message if missing
4. Script evaluates three models on the same WildGuard pair_eval subset:
   - Row 1: pair classifier (RoBERTa-base fine-tuned at `resources/models/llm-safety-monitor/pair-2026-06-07/`)
   - Row 2: llama-guard3 (via Ollama at `http://localhost:11434`)
   - Row 3: Perspective API (skipped if `PERSPECTIVE_API_KEY` env var absent; row shows "–")
5. Output table shows per-model: F1, precision, recall, latency p50 (ms), latency p95 (ms), sample count
6. Results written to `projects/llm-safety-monitor-training/benchmarks/baseline-comparison.md`
7. Script is idempotent: same seed, same results on re-run
8. `--max-samples N` optional flag (default: all ~2300) to allow a fast smoke run during development
9. `--ollama-url` optional flag (default: `http://localhost:11434`) for non-default Ollama ports

---

## Technology Stack

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | — (matches training project) |
| Package manager | uv | — |
| Linter | ruff | — |
| Ollama client | `openai` SDK (OpenAI-compatible API) | Same pattern used in `bias.py`; already familiar |
| ML eval | `sklearn.metrics` | Already in training project deps |
| Classifier inference | `transformers`, `torch` | Already in training project deps |
| Testing | pytest | Already configured |

New dependency: `openai` — add to `projects/llm-safety-monitor-training/pyproject.toml`.

---

## File and Module Structure

All changes are inside `projects/llm-safety-monitor-training/`:

```
projects/llm-safety-monitor-training/
├── llm_safety_training/
│   └── compare_baselines.py     ← new: eval script (all logic in one module)
├── benchmarks/                  ← new directory (created by script on first run)
│   └── baseline-comparison.md  ← output: markdown table written by script
└── pyproject.toml               ← add openai dep + compare-baselines entry point
```

No new test file needed — the script is a one-shot CLI runner, not a library. Correctness is verified by running it end-to-end and inspecting the output table.

---

## Implementation Notes for Architect / Implementer

Since this is a single-file eval script (no data models, no API, no DB), no separate architect output is needed. Notes for the implementer:

**Pair classifier evaluation:**
```python
from llm_safety_training.evaluate import evaluate_binary
from llm_safety_training.datasets import split_wildguard

splits = split_wildguard(seed=42)
result = evaluate_binary("pair", Path("...pair-2026-06-07"), splits.pair_eval_texts, splits.pair_eval_labels)
```

**Llama Guard 3 evaluation:**
```python
import openai
client = openai.OpenAI(base_url="http://localhost:11434/v1", api_key="local")

for text in texts:
    parts = text.split(" [SEP] ", 1)
    prompt, response = parts[0], (parts[1] if len(parts) > 1 else "")
    messages = [{"role": "user", "content": prompt}]
    if response:
        messages.append({"role": "assistant", "content": response})
    
    t0 = time.perf_counter()
    out = client.chat.completions.create(model="llama-guard3", messages=messages, max_tokens=20)
    latency_ms = (time.perf_counter() - t0) * 1000
    
    text_out = (out.choices[0].message.content or "").strip().lower()
    pred = 0 if text_out.startswith("safe") else 1
```

**Checkpoint path** (absolute, derived from workspace root):
- Workspace root: detect via `Path(__file__).parents[3]` (script is at `llm_safety_training/compare_baselines.py`, so `parents[3]` = `muppet-labs/`)
- Pair checkpoint: `workspace_root / "resources/models/llm-safety-monitor/pair-2026-06-07"`

**Output table format** (`benchmarks/baseline-comparison.md`):
```markdown
| Model | F1 | Precision | Recall | Latency p50 (ms) | Latency p95 (ms) | N |
|-------|----|-----------|--------|-----------------|-----------------|---|
| pair-classifier (RoBERTa-base) | 0.xxx | 0.xxx | 0.xxx | – | – | 2317 |
| llama-guard3 (Ollama) | 0.xxx | 0.xxx | 0.xxx | xxx | xxx | 2317 |
| Perspective API | – | – | – | – | – | skipped |
```

**Ollama presence check** before running:
```python
import subprocess
result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
if "llama-guard3" not in result.stdout:
    sys.exit("llama-guard3 not found. Run: ollama pull llama-guard3")
```

---

## Risk Flags

**R1 — Llama Guard 3 output format variance:** The model sometimes outputs `"unsafe\nS1"` or `"safe\n"` — parsing `startswith("safe")` / `startswith("unsafe")` handles both. Log any unparseable outputs and treat as safe (label=0) with a warning count in the report.

**R2 — Inference time:** ~2300 samples at 1–2s/sample = 38–77 minutes. The `--max-samples 200` flag enables a smoke run to verify correctness before committing to the full eval. Document in the `Running locally` section.

**R3 — Workspace root detection:** `Path(__file__).parents[3]` assumes `compare_baselines.py` is exactly 3 directories deep from workspace root (`llm_safety_training/compare_baselines.py` → `llm-safety-monitor-training/` → `projects/` → `muppet-labs/`). Verify before shipping.

**R4 — `openai` not in training deps:** Must add `openai` to `pyproject.toml` dependencies before `uv run compare-baselines` will work.

---

## Handoff

Next role: implementer  
Reads this output to write `llm_safety_training/compare_baselines.py`. No architect pass needed — the design is fully specified above. Implementer should:
1. Add `openai` to training project deps via `uv add openai`
2. Write `compare_baselines.py` per the implementation notes
3. Add entry point to `pyproject.toml`
4. Do a smoke run with `--max-samples 50` to verify Llama Guard 3 integration before the full eval
5. Run full eval (~1h unattended), write `benchmarks/baseline-comparison.md`
6. Add `benchmarks/baseline-comparison.md` reference to `projects/llm-safety-monitor/SUMMARY.md` with honest framing

**Human sign-off required before implementation starts.**
