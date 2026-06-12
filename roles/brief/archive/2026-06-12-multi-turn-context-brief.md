# Brief — Multi-Turn Context Extension

**Sequence:** `new-project-full` | **Role:** brief | **Step:** 1 of N  
**Date:** 2026-06-12

---

## Project Name

multi-turn-context

---

## Description

An extension to the LLM Safety Monitor that adds conversation history to the pair classifier's input, then measures whether classifying the last N turns together changes the detection rate on the existing red-team attack corpus — answering whether single-turn classification misses harms that only become visible in conversational context.

---

## Language(s)

Python (llm-safety-monitor backend + llm-safety-classifier package); TypeScript (minor dashboard update to show turn count per event)

---

## Success Criteria

1. The `LLMInteractionEvent` schema gains an optional `conversation_id` and `turn_index` field
2. The pair classifier's `build_input_text` function gains a `context_turns` parameter: when provided, prepends the last N turn summaries to the classification input
3. A configurable `CONTEXT_WINDOW_TURNS` env var (default 3) controls how many prior turns are included
4. A replay script (`uv run replay-redteam --context-turns 3`) re-classifies the existing 1,797 red-team events using multi-turn context and records results in a new `classifications` row with `classifier_version` bumped
5. A comparison table is produced: single-turn ASR detection rate vs multi-turn ASR detection rate per strategy
6. Results written to `benchmarks/multi-turn-comparison.md`
7. All existing tests continue to pass; new context-window logic has unit tests (≥5)

---

## Constraints

- The red-team attack corpus is single-turn by construction (each attack is one prompt + one response) — multi-turn context for the replay experiment is synthetic: the N prior turns are the N preceding attacks in the same session, ordered by created_at
- The live pipeline change (adding context to real-time classification) is in scope only if the replay experiment shows a meaningful detection rate change (>5% delta); otherwise documented as future work
- No changes to the Kafka message schema in v1 (conversation_id/turn_index are stored in the DB only, not in the Kafka event)
- `llm-safety-classifier` package version bump required; both monitor and red-team venvs must re-sync

---

## Out of Scope

- Multi-turn attack strategies in the red-team runner (attacks remain single-turn)
- Conversation threading in the review UI
- Changes to the prompt or taxonomy classifier (pair only in v1)
- Long-context fine-tuning of the pair classifier

---

## Assumptions

- The synthetic multi-turn context (using prior attacks in the same session as "history") is a reasonable approximation for the experiment, even though real conversations would have coherent topic threading
- The detection rate change may be small or zero — a null result here is a valid and honest finding (single-turn classification is sufficient for this corpus)
- RoBERTa-base has a 512-token limit; N prior turns must be truncated to fit; N=3 short turns should stay within budget

---

## Handoff

Next role: planner  
The planner must decide: whether to modify the existing `classifications` table (new `context_turns` column) or write replay results to a separate `replay_classifications` table; exact truncation strategy when context exceeds 512 tokens; whether the live pipeline change is in scope for v1 or deferred pending experiment results. The replay-first approach is strongly recommended — measure before shipping the live change.
