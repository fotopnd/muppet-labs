# Retro — llm-safety-monitor

**Role:** retro
**Sequence:** `new-project-full`
**Date:** 2026-06-06

---

## Project

**Name:** llm-safety-monitor (project 29)
**Sequence:** new-project-full
**Sessions:** 1 (brief through retro in a single session)
**Roles that ran:** brief → planner → architect → implementer → reviewer → implementer-fixes → retro
**Outcome:** PASS WITH NOTES → all fixes applied → 25/25 tests passing

---

## What Went Well

**1 — Implementer handoff quality**
The implementer's Handoff section named five specific review priorities with file locations and the exact design question for each (JSONB deviation, escalation precedence, DisagreementsResponse reuse, WildGuard categories, patch target). The reviewer was able to open the right files immediately rather than doing a full manifest scan. This is the pattern the handoff section is designed for. Worth reinforcing.

**2 — Deferred imports followed correctly throughout**
All three consumer classes deferred `transformers` imports inside `_load_model` and `classify`. Tests patched at `transformers.AutoTokenizer.from_pretrained` (the source) as the convention requires. No test failures from import patching. The convention added after project 8 held.

**3 — Escalation matrix as pure function**
`compute_escalation_reason` is pure — no DB, no IO, no side effects. This made it trivially testable: 8 unit tests, no fixtures, no mocks. The pattern (push business logic into pure functions; delegate DB work to the outer loop) kept the test surface clean.

**4 — WildGuard category verification caught before training**
The wrong categories were identified during the reviewer session before any training run. Correcting post-training would have required re-running all three models (~6h). The convention of flagging Known Gaps explicitly in the implementer output.md, and the reviewer treating them as must-address, worked as intended.

---

## What Could Have Gone Better

**1 — WILDGUARD_CATEGORIES used wrong taxonomy entirely**
The implementer used MLCommons AI Safety taxonomy names (Title Case) instead of verifying against the actual dataset field values (snake_case). The two taxonomies are completely different. If training had run without verification, the taxonomy classifier would have silently mapped every example to an all-zero label vector for 13 of 13 categories.

- Root cause: No convention for "verify dataset field values as code constants before use." The implementer assumed the model card description matched the raw field values — it did not.
- What would have prevented it: A one-liner `load_dataset(..., split='train[:10]')` + field inspection at the end of the implementer pass.

**2 — Dataset name was wrong (`allenai/wildguard` → `allenai/wildguardmix`)**
The model is `allenai/wildguard`; the dataset is `allenai/wildguardmix`. They are separately gated. The implementer used the model page as the dataset reference. This caused an extra access-request round-trip during verification.

- Root cause: No note that HuggingFace model and dataset are distinct resources, often with different names and separate access controls.
- What would have prevented it: A lookup step: always navigate to `huggingface.co/datasets/` directly rather than inferring the dataset path from the model name.

**3 — SQLAlchemy engine created per Kafka message (C2)**
`create_engine` was called inside `_write_classification` — once per message. This is a well-known SQLAlchemy anti-pattern that causes connection pool exhaustion under load. No convention covered it.

- Root cause: python-conventions.md has no SQLAlchemy section.
- What would have prevented it: A one-line note about engine lifecycle: create once per process, not per call.

**4 — Disagreement total computed from Python-filtered slice (C3)**
The endpoint fetched 200 rows and filtered in Python, then set `total=len(samples)`. This makes `total` wrong when there are >200 rows. The existing aggregation convention says "assert computed outputs not just shape" — but it does not explicitly say "never derive total from a Python slice."

- Root cause: The convention covers test assertions, not the implementation pattern.
- What would have prevented it: Strengthen the aggregation note: push filters to SQL; derive counts via `COUNT(*)`.

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| Reviewer | Loaded all 50+ code files from the manifest | Medium | Implementer Handoff section already ranked priority files — reviewer should load priority files first, then scan others if needed. No structural change required; the pattern worked. |
| Implementer output.md | "How to Run" and "Setup Steps Taken" sections (40 lines) provide no signal for the reviewer | Low | These are useful for the human but reviewer can skip them. Add a note to routing.md: reviewer reads Handoff + Deviations + Known Gaps first; How to Run is human-facing only. |

### Redundancy Patterns

- `WILDGUARD_CATEGORIES` was defined identically in both `types.py` (streaming app) and `datasets.py` (training project). These are separate uv projects so sharing via import isn't possible, but the duplication means a correction must be applied twice. Acceptable given the project boundaries; not a workspace issue.

### Scoping Recommendations

- No significant scoping changes needed. Reviewer loaded what it needed; context was within normal bounds for a project of this size.

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `resources/python-conventions.md` | Add **SQLAlchemy** section: "`create_engine` is expensive — call once per process, not per request or message. Store as a class attribute or module-level singleton. Never call inside a hot loop (Kafka consumer, background worker, request handler)." | C2 would not have occurred with this note in scope | No |
| `resources/python-conventions.md` | Strengthen **Aggregation endpoints** note: append "Never filter in Python what can be filtered in SQL. `total` / `count` fields in API responses must come from a SQL `COUNT(*)`, not from `len()` on a Python-filtered slice." | C3 pattern | No |
| `resources/python-conventions.md` | Add to **HuggingFace Trainer** section: "Before using dataset field values as code constants (label strings, category names), verify exact values programmatically: `load_dataset(..., split='train[:20]')` → inspect field values. Do not infer field values from the model card description — they often differ. HuggingFace model and dataset are distinct resources with different paths and separate gating (e.g. model: `allenai/wildguard`, dataset: `allenai/wildguardmix`)." | Prevents WILDGUARD_CATEGORIES class of error on every future HF training project | No |

### Skills to Update

None required.

### Routing Changes

None required. `new-project-full` was the right sequence and ran cleanly.

### New Resources or Skills Needed

None. All findings map to additions in python-conventions.md.

---

## One Change to Make Now

**Add SQLAlchemy engine lifecycle note to `resources/python-conventions.md`.**

Under the existing `## Error Handling` or as a new `## SQLAlchemy` section, add:

```
## SQLAlchemy

- `create_engine` allocates a connection pool — call it once per process, not per request, message, or loop iteration.
- Store the engine as a class attribute (created in `__init__`) or module-level singleton.
- Never call `create_engine` inside a Kafka consumer loop, FastAPI route handler, or background worker tick.
```

This is the highest-value change: it prevents C2 in every future project that combines SQLAlchemy with a hot loop, and the pattern (Kafka consumers, background pollers) will recur frequently in this workspace.

---

## Handoff

Human reviews recommendations above. Apply the three python-conventions.md additions before the next project starts — they are all No on human decision required.

Update `_config/project-state.md` to record retro complete.
