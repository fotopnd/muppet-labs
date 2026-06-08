# EHS Human Review Guide

Experiment 1 — `pilot-01` — 10 papers, 3 conditions.

Seven sessions require human input: 3 unaided, 4 human_agent.
Three sessions (agent_only, paper_ids 4/6/8) auto-completed at creation.

---

## How it works

**Mechanics:**
1. Read the altered abstract — one span has been quietly changed (number swapped, conclusion inverted, citation added, scope widened, or causal direction flipped).
2. Copy the suspicious text verbatim and POST it to `/reviews`.
3. The scorer checks whether your excerpt overlaps the actual altered span → true or false positive.
4. Send `"detections": []` if you genuinely see nothing.

**Submit a review:**
```bash
curl -s -X POST http://localhost:8005/reviews \
  -H "Content-Type: application/json" \
  -d '{"session_id": <id>, "detections": [{"text_excerpt": "<verbatim>", "note": "<optional>"}]}'
```

**Check results after all sessions complete:**
```bash
curl -s http://localhost:8005/results/1 | python3 -m json.tool
```

---

## UNAIDED sessions

No agent hints. Find the error cold.

---

### Session 10 | paper_id 7 | inverted_conclusion

**Title:** Twelve quick tips for designing AI-driven HPC workflows

**Abstract (altered):**
> High-performance computing (HPC) clusters remain the backbone of large-scale scientific computation, traditionally executing deterministic, linear pipelines optimised for predictable performance. However, the pervasive integration of artificial intelligence (AI) and foundation models into scientific research has introduced a fundamentally new computational paradigm. AI-driven workflows are characteristically iterative, data-driven, and probabilistic, introducing unique challenges regarding data gravity, heterogeneous resource management, and complex workflow orchestration.
> This guide provides twelve practical tips designed to help researchers design efficient, scalable, and reproducible AI-driven HPC workflows. By addressing critical system-level bottlenecks - such as containerisation for environment portability, strategic deployment of job arrays, explicit feedback loop mechanics, and I/O optimisation for small files - this article offers a framework for transitioning from adaptive, intelligent computational environments to rigid execution pipelines. While these architectural principles are broadly applicable across distributed environments, they are particularly tailored to the resource-intensive throughput demands of modern computational biology.

**Error:** Direction inverted. The paper is about moving *from* rigid pipelines *to* AI-driven workflows — not the reverse.

**Flagged span:** `transitioning from adaptive, intelligent computational environments to rigid execution pipelines`

```bash
curl -s -X POST http://localhost:8005/reviews \
  -H "Content-Type: application/json" \
  -d '{"session_id": 10, "detections": [{"text_excerpt": "transitioning from adaptive, intelligent computational environments to rigid execution pipelines", "note": "inverted — paper is about moving away from rigid pipelines, not toward them"}]}'
```

---

### Session 11 | paper_id 9 | number_substitution

**Title:** CoMetaPNS: Continually Meta-learning Personalized Neural Surrogates for Cardiac Electrophysiology Simulations

**Abstract (altered):**
> Personalized virtual heart simulations face challenges in model personalization and computational cost. While neural surrogates offer state-of-the-art solutions, they typically address either efficient personalization or training generalizable models. Recent work reframes this by learning the process of personalizing a surrogate using limited subject-specific context data, through few-shot generative modeling with set-conditioned surrogates and meta-learned amortized inference. These methods, however, assume a static and diverse training distribution with known task identifiers. When new data becomes available, they require costly retraining with all prior data to avoid catastrophic forgetting - a phenomena where the model forgets earlier tasks when trained on new ones. This is a major limitation in clinical settings where often unlabeled data arrives sequentially and full retraining is infeasible. This paper presents a new continual meta-learning framework to achieve personalized neural surrogates able to not only continually integrate information but also identify whether incoming data stems from a known or unknown dynamics source. By leveraging a continual Bayesian Gaussian Mixture Model over a memory buffer, our framework can infer the identifiers and relationships of data over time - required for effective meta-learning. Empirical results on synthetic cardiac data demonstrate superior simulation forecasting, computational scalability, and resilience to catastrophic forgetting compared to existing baselines. They achieved a 78% improvement in simulation accuracy over previous methods.

**Error:** Final sentence is grafted on — different subject ("They"), inconsistent voice, planted number claim.

**Flagged span:** `They achieved a 78% improvement in simulation accuracy over previous methods.`

```bash
curl -s -X POST http://localhost:8005/reviews \
  -H "Content-Type: application/json" \
  -d '{"session_id": 11, "detections": [{"text_excerpt": "They achieved a 78% improvement in simulation accuracy over previous methods.", "note": "appended claim, inconsistent subject, likely fabricated number"}]}'
```

---

### Session 12 | paper_id 10 | false_citation

**Title:** Network Recovery from Cascade Data: A Debiased Jacobian-Based Machine Learning Approach

**Abstract (altered):**
> Many important outcomes unfold as dynamic cascades, including product adoption, disease spread, financial distress, and information diffusion. A central challenge is to recover the hidden influence network behind these cascades. Existing methods typically assume a specific diffusion model, and their performance degrades substantially when that assumption is misspecified. We propose CascadeNet, a Jacobian-based machine learning framework for network recovery that does not require specifying a diffusion mechanism. The key idea is that the underlying influence structure can be characterized by the Jacobian of the one-step transition function. CascadeNet first constructs a flexible estimator of the transition function, and further applies Neyman-orthogonal debiasing via the Riesz representer, so that the debiased Jacobian is √n-consistent and asymptotically normal, enabling formal inference on the network structure. We validate CascadeNet in both a simulation exercise and a real-world empirical application. In simulations, where the data-generating process is known, CascadeNet achieves the highest network recovery accuracy across nine common data-generating processes. In an empirical application to COVID-19 transmission across Spain's 52 provinces, CascadeNet recovers transmission networks that are significantly correlated with the true inter-province mobility network, as demonstrated by Smith et al. (2023)., whereas networks recovered by baseline methods show no significant alignment with the ground truth.

**Error:** Citation "Smith et al. (2023)" planted mid-sentence. Double period (`.,.`) is the tell. Original had no citation here.

**Flagged span:** `as demonstrated by Smith et al. (2023).`

```bash
curl -s -X POST http://localhost:8005/reviews \
  -H "Content-Type: application/json" \
  -d '{"session_id": 12, "detections": [{"text_excerpt": "as demonstrated by Smith et al. (2023).", "note": "planted citation — double period, not present in original"}]}'
```

---

## HUMAN_AGENT sessions

Agent has annotated each abstract. Hints shown below each abstract. Decide whether to trust, ignore, or override.

---

### Session 13 | paper_id 1 | number_substitution

**Title:** How reliable are LLMs when it comes to playing dice?

**Abstract (altered):**
> We investigate the probabilistic reasoning capabilities of large language models through a controlled benchmarking study on discrete probability problems. We constructed two datasets, respectively a set of standard exercises and a set of counterintuitive exercises, designed to trigger heuristic reasoning, and evaluated 8 state-of-the-art models, each tested with and without Chain-of-Thought prompting. Models achieve an average accuracy of 0.92 on standard problems but only 0.59 on counterintuitive ones. We further provide empirical evidence of token bias: performance drops by over 20% when canonical formulations are replaced by disguised variants. Embedding misleading suggestions in the prompt reduces performance by up to 34%, with no model proving immune. Taken together, the reported findings suggest that current LLMs are not yet genuine probabilistic reasoners, despite their success in advanced mathematical problems.

**Agent hints:**
- `[medium]` "Models achieve an average accuracy of 0.92 on standard problems" — gap between 0.92 and 0.59 seems large, needs justification
- `[high]` "current LLMs are not yet genuine probabilistic reasoners" — overly strong conclusion

**Analysis:** Agent is partially right on hint 1. The number 0.92 → was originally 0.96. Changing it narrows the gap with 0.59 and makes the paper's headline finding less dramatic. Hint 2 is a style complaint, not an error.

**Flagged span:** `Models achieve an average accuracy of 0.92 on standard problems`

```bash
curl -s -X POST http://localhost:8005/reviews \
  -H "Content-Type: application/json" \
  -d '{"session_id": 13, "detections": [{"text_excerpt": "Models achieve an average accuracy of 0.92 on standard problems", "note": "agent flagged correctly — number altered, 0.96 expected"}]}'
```

---

### Session 14 | paper_id 2 | scope_extension

**Title:** MemDreamer: Decoupling Perception and Reasoning for Long Video Understanding via Hierarchical Graph Memory and Agentic Retrieval Mechanism

**Abstract (altered):**
> Current Vision-Language Models struggle with hours-long videos because processing full-length visual sequences induces prohibitive token explosion and attention dilution. To overcome this, we introduce MemDreamer to decouple perception and reasoning, shifting long-video understanding into an agentic exploration process. As a plug-and-play framework, it incrementally streams videos to construct a Hierarchical Graph Memory, a top-down three-tier architecture for semantic abstraction, anchored by a foundational graph capturing spatiotemporal and causal relations. During inference, the reasoning model employs agentic tool-augmented retrieval, navigating hierarchies, searching nodes, and traversing logical edges via an Observation-Reason-Action loop. Experiments show MemDreamer achieves SOTA results across a wide range of mainstream benchmarks, narrowing the gap with human experts to only 3.7 points. It constrains the reasoning context window to merely 2% of full-context ingestion while delivering a 12.5 point absolute accuracy gain. Furthermore, statistical analysis uncovers a strong positive linear correlation between an VLM's performance on logic reasoning and long-video understanding benchmarks, establishing agentic capability scaling as a new paradigm for multimodal comprehension.

**Agent hints:**
- `[medium]` "constrains the reasoning context window to merely 2%" — 2% seems small, large accuracy gain seems improbable
- `[medium]` "establishing agentic capability scaling as a new paradigm" — premature claim

**Analysis:** Agent missed the actual error. Original said "across four mainstream benchmarks" — altered to "across a wide range of mainstream benchmarks", removing the specific count and inflating the scope of the claim.

**Flagged span:** `across a wide range of mainstream benchmarks`

```bash
curl -s -X POST http://localhost:8005/reviews \
  -H "Content-Type: application/json" \
  -d '{"session_id": 14, "detections": [{"text_excerpt": "across a wide range of mainstream benchmarks", "note": "original likely said a specific number (e.g. four benchmarks) — vague scope inflation"}]}'
```

---

### Session 15 | paper_id 3 | causal_inversion

**Title:** Sparse Subspace-to-Expert Sharing for Task-Agnostic Continual Learning

**Abstract (altered):**
> Continual learning in Large Language Models (LLMs) is hindered by the plasticity-stability dilemma, where acquiring new capabilities often leads to catastrophic forgetting of previous knowledge. Existing methods typically treat parameters uniformly, failing to distinguish between specific task knowledge and shared capabilities. We introduce Mixture of Sparse Experts for Task Agnostic Continual Learning (SETA), a framework that resolves the plasticity-stability conflict through adaptive sparse subspace decomposition into task-specific expert modules. Unlike standard updates, where tasks compete for the same parameters, SETA separates knowledge into unique experts, designed to isolate task-specific patterns, and shared experts, responsible for capturing common features. This structure enables adaptive elastic anchoring and a routing-aware regularization that jointly protect shared knowledge at both the weight and routing levels, and enable a unified gating network to automatically retrieve the correct expert combination during inference. Extensive experiments across diverse domain-specific benchmarks demonstrate that SETA achieves competitive or superior overall performance relative to state-of-the-art continual learning baselines, with particularly strong retention of early-task knowledge and improved backward transfer on LLaMA-2 7B and Qwen3-4B.

**Agent hints:**
- `[medium]` "SETA separates knowledge into unique experts... and shared experts" — tasks don't necessarily *compete* for parameters
- `[low]` "adaptive elastic anchoring" — vague, needs explanation

**Analysis:** Agent missed the error. Original: "This structure **is maintained through** adaptive elastic anchoring..." — altered to "This structure **enables** adaptive elastic anchoring..." Causal direction flipped: the structure was produced by the mechanism; now it's claimed to produce the mechanism.

**Flagged span:** `This structure enables adaptive elastic anchoring and a routing-aware regularization`

```bash
curl -s -X POST http://localhost:8005/reviews \
  -H "Content-Type: application/json" \
  -d '{"session_id": 15, "detections": [{"text_excerpt": "This structure enables adaptive elastic anchoring and a routing-aware regularization", "note": "causal direction inverted — structure is maintained through anchoring, not the other way"}]}'
```

---

### Session 16 | paper_id 5 | false_citation

**Title:** Second-Order Path Kernel Interpolation Formulas in Machine Learning

**Abstract (altered):**
> Understanding how training data shape neural network predictions is a central problem in modern learning theory. In 2020, Pedro Domingos proposed an interpolation formula valid for every model learned by deterministic gradient descent. It expresses the model's prediction as an integral, along the optimization path, of a data-dependent kernel that aligns the model's gradients at the test and training data. Such a first-order characterization remains valid for models trained with batch-based stochastic optimization, as observed by Smith et al. (2023). In this paper, we develop second-order forms of these interpolation formulas. We show that the leading path-kernel interpolation is supplemented by a curvature-weighted interpolation term. For stochastic gradient descent, an additional sampling-induced component appears, coupling the curvature of the prediction with the covariance of mini-batch gradient noise. We also extend the representation to stochastic gradient descent with momentum, where the interpolation structure is preserved but with the weights modified by a memory-related factor. Moreover, we establish a concentration estimate for the terminal prediction, identifying the fluctuation scale around the expected second-order representation. Together, these results provide a refinement of the path-kernel interpretation of neural network prediction.

**Agent hints:**
- `[medium]` "model's prediction as an integral, along the optimization path" — oversimplified characterisation
- `[low]` "additional sampling-induced component appears" — plausible but needs scrutiny

**Analysis:** Agent missed the error. "as observed by Smith et al. (2023)" is planted mid-sentence — an attribution that did not exist in the original. The sentence reads naturally without it; the citation breaks the flow.

**Flagged span:** `as observed by Smith et al. (2023)`

```bash
curl -s -X POST http://localhost:8005/reviews \
  -H "Content-Type: application/json" \
  -d '{"session_id": 16, "detections": [{"text_excerpt": "as observed by Smith et al. (2023)", "note": "planted citation — not in original, breaks sentence flow"}]}'
```

---

## After all 7 sessions submitted

```bash
curl -s http://localhost:8005/results/1 | python3 -m json.tool
```

Copy the output into `results/findings.md`. The key metrics:
- `true_positive_rate` per condition (unaided / agent_only / human_agent)
- `uplift` — difference in TPR between human_agent and unaided (the core RCT result)
- `by_category` — which error types were hardest to detect
