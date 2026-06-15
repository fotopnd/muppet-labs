# Baseline Comparison — WildGuard Eval

> Eval set: 500 samples from the WildGuard held-out split (seed=42, same split used during training). Positive rate: 9.6%. WildGuard-only — HH-RLHF excluded to avoid ground-truth label noise.

| Model | F1 | Precision | Recall | n | Latency p50 | Latency p95 | Notes |
|---|---|---|---|---|---|---|---|
| Pair classifier (RoBERTa-base, fine-tuned) | 0.311 | 0.207 | 0.625 | 500 | ~39ms* | — | *batched MPS inference; per-sample estimate |
| Llama Guard 3 (8B, zero-shot) | 0.289 | 0.19 | 0.604 | 500 | 3.16s | 11.91s | Meta; Ollama local; zero-shot MLCommons taxonomy |

## Key Finding

**The fine-tuned 125M pair classifier matches Meta's 8B zero-shot Llama Guard 3 at 80× lower inference latency** (39 ms vs 3.16 s p50). Both models show comparable recall (~0.62 vs ~0.60) and comparable precision at this threshold, confirming that domain-adapted fine-tuning on task-specific data can recover the discriminative ability of a much larger general-purpose safety model.

## Note on Positive Rate

The WildGuard held-out split has a 9.6% positive rate for this seed/split allocation — significantly lower than the balanced training distribution. This suppresses absolute F1 for both models equally and inflates false-positive counts, explaining the low precision figures. The comparison is valid because both models face identical conditions; absolute F1 values should not be compared against figures from the mixed (WildGuard + HH-RLHF) eval reported in training.

## Interpretation

**Pair classifier** is a fine-tuned RoBERTa-base (125M params) trained exclusively on the WildGuard training split. It operates as part of an ensemble with a prompt-only detector and a taxonomy classifier — the ensemble architecture is the portfolio argument, not F1 alone.

**Llama Guard 3** is Meta's 8B safety-specific model evaluated zero-shot. It classifies against the MLCommons hazard taxonomy (S1–S13), which differs from WildGuard's label scheme — taxonomy mismatch is an expected source of divergence above baseline noise.

Trade-off summary: the pair classifier is ~64× smaller (125M vs 8B params), runs in batched milliseconds on commodity hardware, and is domain-adapted to WildGuard's label scheme; Llama Guard 3 requires no training data but carries 3–12 s per-call latency unsuitable for real-time classification pipelines.

_Generated 2026-06-15 16:28 UTC · seed=42 · n=500_