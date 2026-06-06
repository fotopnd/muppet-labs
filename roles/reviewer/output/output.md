# Reviewer Output — llm-safety-monitor

**Role:** reviewer
**Sequence:** new-project-full (step 7)
**Date:** 2026-06-06

---

## Summary

The implementation is structurally sound: consumers, escalation poller, API, and frontend are all present and 23+24 tests pass. The most impactful finding is C2 — a new SQLAlchemy engine is instantiated per Kafka message, which will exhaust Postgres connections under production load. C3 (disagreements total undercount) and C4 (escalation_reason silently dropped in `/cases`) are next. T1 and T2 are test coverage gaps required by conventions. Recommended next action: one implementer pass addressing C2, C3, C4, T1, T2 before deploy.

---

## Correctness

**C1 — Dead `MODEL_DISAGREEMENT` branch in escalation router (WARNING)**
- `llm_safety_monitor/escalation/router.py:42-43`
- The branch `if pair_label == 1 and not taxonomy_labels: return MODEL_DISAGREEMENT` is unreachable. All `pair_label == 1` cases return at lines 33 (JAILBREAK) and 35 (BENIGN_HARMFUL) before line 42 is reached. `pair_label` is necessarily 0 at this point.
- The case "pair says unsafe, taxonomy says nothing" is absorbed by BENIGN_HARMFUL — a valid precedence decision. The test `test_model_disagreement_pair_unsafe_taxonomy_clean` correctly documents this. Remove the dead branch and add a comment at line 35 noting that pair=1+prompt=0 classifies as BENIGN_HARMFUL regardless of taxonomy output.
- Severity: **warning** (behaviour is correctly tested; dead code is misleading, not wrong)

**C2 — New SQLAlchemy engine created per Kafka message (WARNING)**
- `llm_safety_monitor/consumers/base.py:46-47`
- `create_engine(self._settings.SYNC_DATABASE_URL)` is called inside `_write_classification`, which runs for every Kafka message. Each call allocates a new connection pool. At ~4 events/second, this will rapidly exhaust Postgres `max_connections` and leave orphaned pool objects.
- Fix: move `create_engine(...)` to `BaseConsumer.__init__`, store as `self._engine`, and use it in `_write_classification`.
- Severity: **warning** (does not manifest in unit tests; will fail under sustained production load)

**C3 — `/metrics/disagreements` total count unreliable above 200 rows (WARNING)**
- `llm_safety_monitor/api/routers/metrics.py:96-123`
- The query fetches 200 rows (all interactions with both pair + taxonomy results) and filters for disagreements in Python. `total=len(samples)` counts only disagreements found within those 200 rows. If there are >200 interactions, the true disagreement count is undercounted.
- Fix: push the disagreement filter to SQL (`WHERE` with pair vs taxonomy contradiction condition) and run a separate `SELECT COUNT(*)` for `total`.
- Severity: **warning** (data accuracy issue; does not crash)

**C4 — `escalation_reason` fetched but silently dropped in `/cases` (MINOR)**
- `llm_safety_monitor/api/routers/review.py:19, 43-51`
- `i.escalation_reason` is selected as `row[2]` in the SQL query but never passed to `DisagreementSample`. Human reviewers see the event and pair/taxonomy labels but not why it was escalated.
- Fix: add `escalation_reason: str | None` to `DisagreementSample` and pass `row[2]` at construction. Alternatively, split to a separate `EscalationCaseSample` schema as the architect intended (see R2).
- Severity: **minor** (missing UX information; nothing is incorrect)

**C5 — ORM `JSON` vs migration `JSONB` type mismatch (MINOR)**
- `llm_safety_monitor/api/models.py:22,51` vs `alembic/versions/001_initial_schema.py:29,61`
- ORM declares `JSON` (cross-dialect; required for SQLite tests); Alembic migration creates `JSONB` columns. PostgreSQL accepts writes from a `JSON`-typed ORM column into a `jsonb` physical column, so runtime behaviour is correct. However `alembic check` will report a pending migration detecting the type difference.
- Implementer's rationale is sound — accept the deviation. Add a comment on the ORM JSON columns documenting the intentional divergence so it isn't "fixed" by a future developer.
- Severity: **minor** (no runtime impact; `alembic check` will be noisy)

---

## Style

**S1 — `ANTHROPIC_API_KEY` defaults to empty string (WARNING)**
- `llm_safety_monitor/config.py:38`
- `ANTHROPIC_API_KEY: str = ""` lets the app start without the key, producing a cryptic authentication error only when live Claude mode triggers. Should be `str | None = None` with a startup validation that raises if `LIVE_CLAUDE_MODE=True and not settings.ANTHROPIC_API_KEY`.

**S2 — Ambiguous variable name `l` (MINOR)**
- `llm_safety_monitor-training/llm_safety_training/datasets.py:266`
- `[l for _, l in train]` — single-character `l` is visually ambiguous (l/1). Rename to `label` or `lbl`.

**S3 — Misleading test function name (MINOR)**
- `projects/llm-safety-monitor/tests/test_escalation.py:49`
- `test_model_disagreement_pair_unsafe_taxonomy_clean` asserts `BENIGN_HARMFUL`, not `MODEL_DISAGREEMENT`. The name contradicts the assertion and will confuse future readers. Rename to `test_benign_harmful_pair_unsafe_prompt_safe`.

---

## Tests

**T1 — `/cases` endpoint has no seeded-data test (WARNING)**
- `tests/test_api.py:107-111` — `test_cases_empty` checks shape only.
- Per `python-conventions.md`: aggregation endpoints need at least one seeded-data test asserting computed output. Add a test that seeds an interaction with a non-`LOG_ONLY` `escalation_reason` and verifies `total >= 1` and a matching sample in the response.

**T2 — `/metrics/disagreements` endpoint has no seeded-data test (WARNING)**
- `tests/test_api.py:99-104` — `test_disagreements_empty` checks shape only.
- Same convention gap. Seed an interaction where `pair_classifier` label=0 and `taxonomy_classifier` has non-empty labels; verify `total >= 1` and at least one sample with correct fields.

**T3 — `EscalationPoller` DB dispatch logic is untested (MINOR)**
- `_check_ready`, `_check_timed_out`, and `_process_event` are only exercisable through `run()` (a daemon). The SQL queries, the escalation reason commit, and the `_post_to_case_queue` call have no unit coverage. Consider unit-testing `_process_event` directly with a mocked `Session` to verify the commit and case-queue dispatch for each escalation branch.

---

## Refactor Candidates

**R1 — Engine per-consumer (same fix as C2)**
- `BaseConsumer.__init__` should call `create_engine(settings.SYNC_DATABASE_URL)` once and store as `self._engine`. `_write_classification` uses `self._engine`.

**R2 — Split `DisagreementsResponse` from escalation schema**
- The architect intended a separate `EscalationQueueResponse`. Currently `DisagreementsResponse` serves both `/metrics/disagreements` and `/cases`. When C4 is fixed (adding `escalation_reason` per sample), the schema split becomes necessary anyway — do both together.

**R3 — SQL-side disagreement filter**
- The in-Python filter at `metrics.py:110-111` works for small volumes. Fixing C3 requires moving this to SQL — do R3 and C3 together.

---

## Verdict

**PASS WITH NOTES** — no blocking issues. Code runs, all tests pass, implementation is structurally complete. One implementer pass is needed before deploy or training.

---

## Handoff

**Next role: implementer.** Address the following (ordered by priority):

**Must fix (conventions + production correctness):**
1. **C2** — Move `create_engine` to `BaseConsumer.__init__`; use `self._engine` in `_write_classification`
2. **T1** — Add seeded test for `GET /cases` asserting `total >= 1` with an escalated interaction
3. **T2** — Add seeded test for `GET /metrics/disagreements` asserting `total >= 1` with a seeded disagreement
4. **C3 + R3** — Push disagreement filter to SQL; use `COUNT(*)` for `total` in `/metrics/disagreements`
5. **C4 + R2** — Add `escalation_reason: str | None` to `DisagreementSample` (or split to `EscalationCaseSample`); wire from `row[2]` in `review.py`

**Address if time permits:**
6. **C1** — Remove dead branch at `router.py:42-43`; add comment at line 35 explaining BENIGN_HARMFUL precedence
7. **S3** — Rename `test_model_disagreement_pair_unsafe_taxonomy_clean` → `test_benign_harmful_pair_unsafe_prompt_safe`
8. **C5** — Add comment on ORM `JSON` columns documenting the intentional JSONB deviation
9. **S1** — Change `ANTHROPIC_API_KEY: str = ""` to `str | None = None`; add startup guard for live mode

**Before training (not a code fix — human action required):**
- **Known Gap 1** — Verify `WILDGUARD_CATEGORIES` against actual dataset schema: `load_dataset("allenai/wildguard")` → inspect `features`. Update both `types.py` and `datasets.py` if names differ. This must happen before any training run or taxonomy labels will be silently wrong.
