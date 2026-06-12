# Error Hide and Seek — Executive Summary

## The Problem

Safety review teams face a practical question that is rarely measured directly: when a human reviewer uses an AI agent to help identify problematic content, does the agent actually improve detection? The intuitive answer is yes, though the intuitive answer is not always correct. Without a controlled measurement, a team has no way to know whether agent hints are helping, hurting, or simply adding noise.

## What Was Built

A randomised controlled trial (RCT) that plants subtle errors into academic paper abstracts, assigns each paper to one of three review conditions (unaided human, AI agent only, or human with AI hints), and measures how often the real error is found versus how often the reviewer raises false alarms. The system runs end-to-end: a planting pipeline generates altered abstracts, a review web interface presents them to the human reviewer, and a scoring engine computes results automatically when each session is submitted.

## Why It Matters

The work provides a concrete, signed answer to a question that is directly relevant to Anthropic's Safeguards work: how much does AI assistance improve human error detection in a review task? The null result (overall uplift of −0.01 across two experiments) is the finding, not a failure. It identifies exactly where AI hints help (structural errors that do not require access to the original text) and where they do not (domain-specific errors that are fundamentally unverifiable without ground-truth access). That distinction matters for how safety review workflows are designed.

## What Was Demonstrated

Two experiments across 100 papers and 67 human review sessions, with results scored per condition and per error category:

| Condition | TPR | FPR |
|-----------|-----|-----|
| Unaided | 0.30 | 0.64 |
| Agent-only | 0.33 | 0.78 |
| Human+Agent | 0.29 | 0.72 |
| **Uplift** | **−0.01** | |

Category-level analysis revealed the one exception: inverted conclusions, which are logical reversals that Claude can identify without domain knowledge, showed +0.33 uplift in the human+agent condition. All domain-dependent categories (number substitution, false citation, causal inversion) showed zero or negative uplift, because no amount of AI reasoning can verify a claim that requires comparing against the original document.

The work demonstrates experimental rigour: honest null results, documented corpus confounds, and category-level decomposition of where the hint effect is positive and where it is not.

## What Extension Would Require

- A domain-expert reviewer cohort to isolate the non-expert confound in the current corpus
- Additional error corpora in domains where the reviewer has existing knowledge
- Time-on-task instrumentation (uplift may appear differently under fatigue conditions)
- Scale: the current RCT harness supports any paper corpus and any LLM backend with configuration changes only

## Appendix: Technical Details

The RCT is backed by a FastAPI/PostgreSQL backend, a React review interface, and a scoring engine that evaluates human detections against planted spans using substring overlap across both the original and altered text. The auto-annotation pipeline calls Claude on session creation so agent annotations are available before the reviewer sees the abstract. The full technical architecture and implementation decisions are in the [Technical Deep-Dive](README.md).
