# Reviewer Output — moderation-stream

**Role:** reviewer
**Sequence:** `new-project-full` (step 8)
**Date:** 2026-06-02
**Reads:** `roles/implementer/output/output.md`, all code files in `projects/moderation-stream/`, frontend additions in `projects/case-queue/web/src/`
**Resources:** `resources/python-conventions.md`, `resources/typescript-conventions.md`

---

## Summary

moderation-stream is architecturally sound and runnable. The Python backend is clean, the async FastAPI metrics API is correct, and the consumer poll loop handles shutdown and Kafka errors correctly. The `flush()`/commit flow in case-queue's `decisions.py` (previously flagged) is confirmed correct. Two warnings stand out: broad exception swallowing in the consumer loop loses stack traces, making production debugging hard; and the test suite has no integration test that inserts rows and asserts computed metric values — the most load-bearing path in the whole system is not covered. The new stream frontend components are also entirely untested. These don't block the portfolio demo but should be addressed before claiming test coverage.

---

## Correctness

### C1 — Resolved: `decisions.py` flush/commit flow is correct (case-queue, previously flagged)

**Severity: None**

The implementer flagged a potential double-commit between `await db.flush()` in `decisions.py:52` and `await session.commit()` in `case-queue/api/app/database.py:34`. This is not a bug. `flush()` sends the INSERT/UPDATE SQL within the open transaction so the immediately following `db.refresh(decision)` can read the new row. The single commit fires when the route handler returns and the `get_db` context manager exits. Correct and idiomatic.

---

### C2 — `consumers/base.py:96` — Broad exception swallows stack trace

**Severity: Warning**

```python
except Exception as exc:
    logger.warning("[%s] Failed to process message: %s", self.model_name, exc)
```

This catches all exceptions including programming errors (`AttributeError`, `KeyError`) that should surface. Convention: "Do not catch broad `Exception` unless it is at a boundary (CLI top-level, retry loops)." The consumer loop is a legitimate boundary — a bad message should not kill the process — but logging only `exc` (not `exc_info=True`) means the traceback is silently dropped. A mistyped field name in a new model would log one line with no location and be undebuggable in production.

**Fix:** `logger.warning("[%s] Failed to process message", self.model_name, exc_info=True)`.

---

### C3 — `producer.py:35` — `ensure_topic` catches broad `Exception` with string match

**Severity: Minor**

```python
except Exception as exc:
    if "already exists" not in str(exc).lower():
        raise
```

The TOCTOU race (list → create) is correct. The catch is fragile: a network error whose message happens to contain "already exists" would be silently swallowed. The correct exception is `KafkaException`; the error code is `TOPIC_ALREADY_EXISTS`. The current code works against a standard Kafka setup but will mask unrelated failures.

**Fix:** `except KafkaException as exc: ...` — imports `KafkaException` (already imported in base.py).

---

### C4 — `conftest.py` — Missing return type annotations on async fixtures

**Severity: Minor**

```python
@pytest_asyncio.fixture(scope="session")
async def test_engine():  # missing -> AsyncGenerator[AsyncEngine, None]

@pytest_asyncio.fixture
async def api_client(test_engine):  # missing -> AsyncGenerator[AsyncClient, None]
```

Convention requires type hints on all function signatures. `test_engine` is also missing a parameter annotation on the `api_client` fixture.

---

### C5 — `metrics.py` — Active model with no DB rows gets zero metrics silently

**Severity: Minor**

In `_build_response`, when a model is `ACTIVE` but has no rows in `classification_results` (i.e., it does not appear in `db_data`), the `else` branch emits zeros for all metrics. This is architecturally intentional (freshly started consumers), but the `status` field will show `active` while `total_processed` is `0`. The frontend correctly renders this (it just shows zeros), but there is no way to distinguish "active consumer processing" from "consumer hasn't been started yet" at the API level. Not a bug, but worth noting for Phase 2 planning.

---

### C6 — `finetuned.py:39` — `_run_inference` returns `0` silently when pipe is `None`

**Severity: Minor**

```python
def _run_inference(self, text: str) -> int:
    if self._pipe is None:
        return 0
```

`run()` exits early if no checkpoint exists, so in practice `_run_inference` is never called with `_pipe = None`. However, the silent `return 0` means that if `run()` were called in a test or incorrectly in production without the early-exit guard, wrong labels would be written to the DB with no log entry. A `raise RuntimeError("cannot run inference — no checkpoint loaded")` would be safer and self-documenting.

---

## Style

### S1 — `config.py:8` — `MODEL_REGISTRY: list[dict[str, Any]]` uses `Any`

Convention: "Never use `Any` as a field type unless the field genuinely holds arbitrary external data." `MODEL_REGISTRY` is internal config, not external data. The `Any` arises because the dict values are heterogeneous (`str`, `int`). A `TypedDict` (`ModelRegistryEntry`) with typed fields eliminates this.

**Refactor candidate R1** covers this.

---

### S2 — `metrics.py:39` — `_build_response` parameter typed `list[Any]`

Same concern as S1. SQLAlchemy `Row` objects from `result.fetchall()` can be typed as `Sequence[Row[Any]]` from `sqlalchemy.engine`. Not blocking but `Any` propagates through the function.

---

### S3 — `ModelMetricsCard.tsx` — Exported component missing explicit return type

Convention: "Prefer explicit types over inference at module boundaries (function return types, exported values)." `ModelMetricsCard` and `MetricRow` both lack `: JSX.Element` return type annotations. `pnpm build` passes — this is a convention deviation only.

---

### S4 — `stream.ts:10` — Unsafe cast `res.json() as Promise<MetricsResponse>`

`res.json()` returns `Promise<unknown>` in strict mode (or `Promise<any>` in practice). Casting directly to `Promise<MetricsResponse>` bypasses runtime validation. Convention says "No `any`. If external data has an unknown shape, use `unknown` and narrow it explicitly." For a portfolio project without Zod, an acceptable middle ground is to assert the type explicitly with a comment explaining validation is deferred. Not blocking since the API and frontend share the same schema definition.

---

## Tests

### T1 — No metrics computation integration test (Warning)

The 6 tests in `test_api.py` verify response shape, model names, and status flags — all with an empty database. The most important correctness property — that `GET /metrics` returns correct `accuracy`, `p50_latency_ms`, `throughput_cps` given real rows — is completely untested.

**What is missing:** A test fixture that inserts a known set of `ClassificationResult` rows (e.g., 10 rows with known latencies, 8 `correct=True`), calls `GET /metrics`, and asserts computed accuracy ≈ 0.8, p50 ≈ known median, throughput > 0.

This is the core value proposition of the system. Without it, a SQL bug in `METRICS_SQL` would pass all tests.

---

### T2 — No tests for new stream frontend components (Warning)

`StreamDashboard.tsx` and `ModelMetricsCard.tsx` have no test files. The rest of the case-queue frontend (`CaseQueue`, `CaseDetail`, `AuditLog`) all have component tests. The stream UI is the primary new user-facing surface in this diff.

**Minimum coverage needed:**
- `ModelMetricsCard.test.tsx`: active state renders all metric rows; pending state renders the awaiting-weights message.
- `StreamDashboard.test.tsx`: loading skeleton renders 5 cards; data renders `ModelMetricsCard` per model; error with no data renders `ErrorMessage`.

---

### T3 — `test_consumers.py:52` — Redundant test

`test_latency_is_non_negative` repeats the `latency_ms >= 0.0` assertion already present in `test_classify_returns_label_and_latency`. No new coverage.

---

### T4 — `publish_events` rate control untested

The rate-limiting logic (`interval`, `time.sleep`) in `producer.py:77–88` is not tested. A test that mocks `time.sleep` and `time.monotonic` could verify the sleep duration is computed correctly. Low priority given the function is straightforward.

---

## Refactor Candidates

| # | Location | Suggestion |
|---|----------|------------|
| R1 | `config.py:8`, `metrics.py:39` | Replace `list[dict[str, Any]]` with a `TypedDict` (`ModelRegistryEntry`) to eliminate `Any` |
| R2 | `consumers/base.py:96` | Change `logger.warning(..., exc)` to `logger.warning(..., exc_info=True)` to preserve tracebacks — one-line fix, high operational value |
| R3 | `producer.py:35` | Narrow `except Exception` to `except KafkaException` |
| R4 | `finetuned.py:39` | Replace `return 0` when `self._pipe is None` with `raise RuntimeError("no checkpoint loaded")` |
| R5 | `conftest.py:16,24` | Add return type annotations to both async fixtures |
| R6 | `ModelMetricsCard.tsx`, `StreamDashboard.tsx` | Add `: JSX.Element` return types to exported components |

R2 is the highest operational value item — a one-character change that makes production debugging possible.

---

## Verdict

**PASS WITH NOTES**

No blocking correctness issues. The commit/flush flow is confirmed correct. The consumer loop, producer, and metrics API are structurally sound. The most important follow-up items are the missing metrics computation test (T1) and stream component tests (T2) — these are warnings, not blockers. R2 (`exc_info=True`) is a one-line fix worth doing immediately.

---

## Handoff

**PASS WITH NOTES** — No next role required unless the human chooses to address the gaps below.

**Recommended implementer pass (prioritised):**
1. **R2** — `logger.warning(..., exc_info=True)` in `base.py:97` — one line, immediate operational value.
2. **T1** — Add a metrics computation integration test: insert known rows, assert computed values.
3. **T2** — Add `ModelMetricsCard.test.tsx` and `StreamDashboard.test.tsx`.
4. **R1** — `TypedDict` for `MODEL_REGISTRY` to eliminate `Any`.

**Project-state update required:** Update `_config/project-state.md` — reviewer step complete, verdict PASS WITH NOTES. Next action: either retro (step 9 of `new-project-full`) or an implementer pass to address T1/T2/R2.
