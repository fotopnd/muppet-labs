# Brief Archive: Wave 3b — llama3.1:8b (2026-06-14)

**Status:** COMPLETE

## What was done
- Preflight: measured llama3.1:8b locally (10.8 tok/s on M4), projected RunPod cost ($5.01–$6.70)
- Migrated to new RTX 5090 pod (previous pod had qwen2.5:7b cached but no llama3.1:8b)
- Pulled llama3.1:8b (~4.7 GB) on new pod, confirmed connectivity
- Ran 13 strategies × 300 attacks vs llama3.1:8b

## Results summary
- Wall time: 1h 56m (vs 2h 48m Wave 3a — llama3.1 faster due to low compliance = short outputs)
- Actual cost: $3.59 (vs $6.70 conservative preflight — well under budget)
- Peak ASR: 16.0% (refusal_suppression) — dramatically more resistant than gemma2:9b (94.7%) and qwen2.5:7b (73%)

## Three-model narrative established
| Model | Company | Peak ASR | Character |
|---|---|---|---|
| gemma2:9b | Google | 94.7% | Most vulnerable — nearly all strategies succeed |
| qwen2.5:7b | Alibaba | 73.0% | Middle — roleplay resistant, injection vulnerable |
| llama3.1:8b | Meta | 16.0% | Most resistant — only obfuscation/suppression break through |

## Defects closed
- D3: 13/35 strategies → remains 13 (all models now cover same 13 strategies)
- D4: Single model → 3 models (Google / Alibaba / Meta comparison live)
