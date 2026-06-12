Assuming Apple Silicon Mac with Ollama, gemma2:9b at ~40 tok/s generation on M2 Pro / equivalent:

┌─────────┬─────────────────────────────────────────────────────────────────────────┬───────────┐
│ Project │                            What runs locally                            │ Estimate  │
├─────────┼─────────────────────────────────────────────────────────────────────────┼───────────┤
│ P3      │ 200 Ollama calls (200 tok avg response) + all-MiniLM similarity scoring │ 25–40 min │
├─────────┼─────────────────────────────────────────────────────────────────────────┼───────────┤
│ P4      │ ~100 RoBERTa-base classifications on CPU                                │ <2 min    │
├─────────┼─────────────────────────────────────────────────────────────────────────┼───────────┤
│ P5      │ 1,797 RoBERTa-base classifications with context prepended on CPU        │ 3–6 min   │
└─────────┴─────────────────────────────────────────────────────────────────────────┴───────────┘

P3 is the only one with meaningful wall clock time, and it's one-shot (seed the corpus, run the attack loop, done).

---
Corpus authoring in detail

P3 — 200 multilingual prompt variants

The corpus is 10 governments × 5 topics × 4 languages. You need to decide the grid before anything can be seeded. Realistic approach:

1. Pick the grid (~30 min human): choose 10 governments (e.g. China, Russia, Iran, Saudi Arabia, North Korea, Turkey, USA, India, EU, Israel) and 5 topic types (e.g. election legitimacy, protest/dissent framing, media freedom, historical atrocity framing, territorial/sovereignty claims). The grid choices drive how non-trivial the divergence signal will be.
2. Write 50 EN prompts (~1 hr, Claude-assisted): one per (gov, topic) pair, phrased as safety-relevant or politically charged queries. These are the canonical variants — the other 3 languages derive from them.
3. Generate ZH/RU/AR variants (~30 min, Claude API): batch-translate/adapt all 50 into each of the 3 other languages. Not machine translation of English syntax — you want prompts that read naturally in each language and might trigger different model behaviour. Claude handles this well in one shot per language.
4. Review 150 non-EN variants (~1–2 hr human): spot-check for meaning drift and obvious errors. You don't need fluency — run a few back through Claude asking "does this say roughly [EN intent]?" for suspicious ones.

Total: 3–4 hours human time, ~50–80 Claude API calls, and produces a static CSV/JSONL file that gets imported once.

P4 — evasion corpus construction

This is more iterative because you need confirmed evasions (classifier predicts safe on something that is actually harmful), which requires a classify→review loop:

1. Select seed prompts (~20 min): pull 20–30 representative harmful prompts from the existing red-team corpus (already in DB at port 5435). These need to be prompts the classifier currently flags correctly — your baseline.
2. Generate variants per strategy (~1 hr, Claude API, 5 batches): for each strategy, prompt Claude to apply the transformation to all seed prompts. ~5 API calls, 20 outputs each = 100 variants.
3. Run classifier on all 100 (<2 min): score every variant, collect predicted_label=0 cases.
4. Human review of evaded examples (~1–2 hr): this is the critical step. For each variant where the classifier said "safe", you confirm it is actually harmful (not a false positive from a bad variant). Some strategies will produce weak variants that aren't really harmful — discard those.
5. Iterate on underperforming strategies (~30–60 min): if a strategy produces fewer than 20 confirmed evasions, prompt Claude for more variants with tighter constraints and re-run.

Total: 3–5 hours across 2 sessions (generation then review). The review step can't be skipped — the brief explicitly flags human sign-off on harmful content.

P5 — no corpus authoring. It replays the existing 1,797 red-team events. No new content needed.

---
Bottom line by project:

┌─────┬─────────────────────────────────┬────────────┬────────┐
│     │           Human time            │ Claude API │ RunPod │
├─────┼─────────────────────────────────┼────────────┼────────┤
│ P3  │ 3–4 hrs (grid design + review)  │ ~$0.50     │ none   │
├─────┼─────────────────────────────────┼────────────┼────────┤
│ P4  │ 3–5 hrs across 2 sessions       │ ~$1–2      │ none   │
├─────┼─────────────────────────────────┼────────────┼────────┤
│ P5  │ <1 hr (code only, no authoring) │ none       │ none   │
└─────┴─────────────────────────────────┴────────────┴────────┘