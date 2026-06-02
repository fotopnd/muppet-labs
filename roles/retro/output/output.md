# Retro — moderation-stream

**Role:** retro
**Sequence:** `new-project-full` (step 9 of 9)
**Date:** 2026-06-02
**Reads:** `roles/reviewer/output/output.md`, `roles/implementer/output/output.md`, `_config/project-state.md`, `resources/routing.md`, `resources/vibecoding-style.md`

---

## Project

**Name:** moderation-stream (project 22)
**Sequence:** `new-project-full`
**Sessions:** 1 (2026-06-02)
**Roles that ran:** brief → planner → architect → design-brief → frontend-architect → implementer → ui-reviewer → ui-debugger → reviewer → implementer pass (R2/T1/T2) → retro
**Languages:** Python (FastAPI, Kafka consumers), TypeScript (React dashboard route in case-queue)
**Key characteristic:** Two-project implementation — new Python service + frontend additions to an existing React app

---

## What Went Well

**1. Phase-gated architecture held from design through frontend.**
The Phase 1 / Phase 2 model split (`MODEL_REGISTRY` + `ModelStatus`) was decided at the architect stage and flowed cleanly through every downstream role. The API returns `pending_weights` for fine-tuned models with no checkpoint; the frontend renders a distinct pending card state; the reviewer confirmed the logic is correct. No rework, no design revisit. Designing the Phase 2 state at architecture time — even though Phase 2 doesn't run yet — meant the frontend could render all five model slots from day one without placeholders or conditional rendering hacks.

**2. Port isolation (5433 vs 5432) was decided once and held.**
Routing Postgres to 5433 to avoid case-queue collision was a one-line decision at the architect stage. It appeared correctly in docker-compose.yml, `.env.example`, the test DB URL, and conftest. No environment collision debugging occurred. Decisions with multi-file impact made cleanly at architecture time are cheaper than any post-implementation fix.

**3. Sync/async split between consumers and API was correct and friction-free.**
Consumers are synchronous (blocking poll loop); the metrics API is fully async. These share a Postgres database but use separate SQLAlchemy engines. The reviewer confirmed no double-commit risk. The implementer's choice to instantiate `create_engine` in `BaseConsumer.__init__` (sync) and `create_async_engine` in the API's lifespan (async) respected the split without any overlap.

**4. Adding the stream dashboard to case-queue required no structural rework.**
The existing `App.tsx` router, `@/` path alias, shadcn/ui library, and TanStack Query provider all absorbed the new `/stream` route cleanly: 4 new files, 3 modified, one `NavLink`, one `Route`. The componentisation from the earlier case-queue build paid dividends here with zero friction.

**5. ui-reviewer caught the blocking tailwind.config.js duplicate `colors` key before any manual testing.**
The duplicate key would have silently broken all shadcn/ui token classes at runtime — invisible to TypeScript and unit tests. Left undetected, this would have produced a confusing "all the cards look wrong" symptom with no obvious cause. The ui-reviewer is the only role in the sequence that catches this class of error. It did its job.

---

## What Could Have Gone Better

**1. `VITE_STREAM_API_URL` missing from `.env.example` — a known gap that shipped.**

The implementer's own output flagged this explicitly: "`VITE_STREAM_API_URL` not in `case-queue/web/.env.example` — must be added manually." The code references `import.meta.env['VITE_STREAM_API_URL']`; the example file doesn't mention it. Anyone following the How to Run instructions starts the frontend and gets a broken `/stream` page with no explanation.

*Root cause:* Frontend env var additions weren't reflected back into `.env.example`. The implementer documented the fix in prose but didn't apply it.

*Prevention:* Convention: "Any new `import.meta.env.VITE_*` reference must have a matching entry in `.env.example` in the same implementer pass." Add to `typescript-conventions.md`.

---

**2. API tests shipped with empty-DB-only coverage for an aggregation-heavy system.**

The core value of moderation-stream is computed metrics — accuracy, p50 latency, throughput. The 6 initial API tests verified response shape and status flags against an empty database. A SQL bug in `METRICS_SQL` would have passed all of them. The reviewer caught the gap; the implementer pass added the seeded-data test. It should have been in the first pass.

*Root cause:* The test plan followed the "verify shape, verify status" pattern appropriate for CRUD endpoints. Aggregation endpoints need a different pattern: seed known data, assert computed outputs.

*Prevention:* Add to `python-conventions.md` under Testing: "For endpoints that aggregate or compute derived values, include at least one test with seeded data that asserts computed outputs, not just response shape."

---

**3. Consumer loop shipped without `exc_info=True` — stack traces silently dropped.**

`except Exception` in `BaseConsumer.run()` logged the exception message but not the traceback. The reviewer flagged it; the implementer pass fixed it in one character. In production, any programming error in the consumer would log a single line with no location.

*Root cause:* `python-conventions.md` correctly says "do not catch broad `Exception` unless at a boundary" but gives no guidance for the legitimate boundary case — what to do when you do catch it.

*Prevention:* Extend Error Handling in `python-conventions.md`: "When catching broad `Exception` at a legitimate boundary (consumer loop, retry handler), always log with `exc_info=True` to preserve the full traceback."

---

**4. `_run_inference` returning `0` silently when no model is loaded is a latent hazard.**

`run()` exits early before `_run_inference` is called with no checkpoint, so this can't happen in practice. But the silent `return 0` means future callers or tests that bypass the early-exit guard would write wrong labels to the database with no error. A `raise RuntimeError` would fail loudly and be self-documenting.

*Root cause:* No convention about methods that require prior initialisation. The `if not ready: return default` pattern is common but produces invisible failures.

*Prevention:* Add to `python-conventions.md` under Error Handling: "Methods requiring prior initialisation (model weights, external connections) should raise on uninitialised state rather than returning a silent default. Prefer `raise RuntimeError(...)` over `if self._pipe is None: return 0`."

---

## Token Efficiency Analysis

### Context Bloat Identified

| Stage | Issue | Estimated Waste | Recommendation |
|-------|-------|-----------------|----------------|
| Retro | `routing.md` loaded in full (216 lines) to confirm which sequence ran and whether it was right | Medium | Project-state.md already names the sequence. Retro role contract should note: skip routing.md if sequence name and completion status are clear from project-state. |
| Implementer | Output covers two project locations in one 284-line file | Low — complexity warranted it | Acceptable. Add a "Scope" H2 early so downstream roles can skip irrelevant sections. |

### Redundancy Patterns

`project-state.md` contains a detailed "Project File Map" for case-queue (60 lines) but none for moderation-stream — the moderation-stream manifest lives only in the implementer output. This is inconsistent and will drift as both projects evolve. Either both projects should have file maps in project-state, or neither should — project-state should link to implementer output instead of re-listing files.

### Scoping Recommendations

The retro loads `routing.md` solely to confirm the sequence used and assess fit. Since `project-state.md` already records "Sequence: `new-project-full`, step N complete", the retro role contract should mark `routing.md` as optional — load only if the sequence choice itself is in question.

---

## Workspace Improvement Recommendations

### Resources to Update

| File | Change | Reason | Human decision required? |
|------|--------|--------|--------------------------|
| `resources/python-conventions.md` | Under **Error Handling**, add: "When catching broad `Exception` at a legitimate boundary (consumer loop, retry handler), always log with `exc_info=True` to preserve the full traceback." | Prevents silent traceback suppression in consumer/loop patterns | No |
| `resources/python-conventions.md` | Under **Error Handling**, add: "Methods requiring prior initialisation (model weights, external connections) should raise on uninitialised state rather than returning a silent default. Prefer `raise RuntimeError(...)` over `if self._pipe is None: return 0`." | Prevents latent silent-default bugs | No |
| `resources/python-conventions.md` | Under **Testing**, add: "For endpoints that aggregate or compute derived values, include at least one test with seeded data that asserts computed outputs, not just response shape." | Prevents empty-DB-only coverage for aggregation endpoints | No |
| `resources/typescript-conventions.md` | Under **Package Management and Tooling**, add: "Any new `import.meta.env.VITE_*` reference must have a matching entry in `.env.example` in the same implementer pass." | Prevents the VITE_STREAM_API_URL gap from recurring | No |

### Skills to Update

No changes needed. `skills/dev-server-setup.md` (created in the case-queue retro) covers the Makefile/startup pattern used correctly here.

### Routing Changes

| Sequence | Change | Reason | Human decision required? |
|----------|--------|--------|--------------------------|
| All sequences | In the retro row of each sequence table, mark `routing.md` as "optional — skip if sequence is named in project-state.md" | Retro loads routing.md only to confirm sequence; project-state already names it | No |

### New Resources or Skills Needed

None. The moderation-stream project surfaced no gaps requiring a new file — only additions to existing ones. `prompt-design.md` and `dev-server-setup.md` recommended in the case-queue retro were both applied and were not needed here.

---

## One Change to Make Now

**Add the `exc_info=True` convention to `resources/python-conventions.md` under Error Handling.**

Exact addition:

```markdown
When catching broad `Exception` at a legitimate boundary (consumer loop, retry handler),
always log with `exc_info=True` to preserve the full traceback:

    except Exception:
        logger.warning("Failed to process message", exc_info=True)

Logging only the exception message drops the stack — undebuggable in production.
```

**Why this one:** The consumer loop is a real deployment target. A message-processing bug in production with the old code yields one log line and no stack trace. The fix is one parameter. It prevents the same miss in every future consumer, retry handler, or batch-processing loop — the class of code where broad catches are legitimately needed. The other three recommendations affect design-time correctness; this one affects runtime operability, which matters more when the system is running.

---

## Handoff

`new-project-full` sequence for moderation-stream is complete.

**Recommended actions (ordered):**
1. Apply the `exc_info=True` addition to `resources/python-conventions.md` (One Change to Make Now).
2. Add the seeded-data testing requirement to `python-conventions.md`.
3. Add the `VITE_*` env example rule to `typescript-conventions.md`.
4. Add the raise-on-uninitialised convention to `python-conventions.md`.
5. Fix the actual gap: add `VITE_STREAM_API_URL=http://localhost:8001` to `projects/case-queue/web/.env.example` (one line, no role required).

**Update `_config/project-state.md`:** Record retro complete, sequence closed, which recommendations were actioned.
