# Author Output — Anthropic Safeguards Portfolio Writeups

## Documents Produced

| # | File | Type | Template | Audience |
|---|------|------|----------|----------|
| 1 | `PORTFOLIO.md` (workspace root) | Portfolio Overview | technical-summary.md (adapted) | Tier 2 + Tier 3 |
| 2 | `projects/error-hide-seek/SUMMARY.md` | Executive Summary | executive-summary.md | Tier 3 |
| 3 | `projects/error-hide-seek/README.md` | Technical Deep-Dive | technical-deep-dive.md | Tier 1 |
| 4 | `projects/red-team-platform/SUMMARY.md` | Executive Summary | executive-summary.md | Tier 3 |
| 5 | `projects/red-team-platform/README.md` | Technical Deep-Dive | technical-deep-dive.md | Tier 1 |
| 6 | `projects/llm-safety-monitor/SUMMARY.md` | Executive Summary | executive-summary.md | Tier 3 |
| 7 | `projects/llm-safety-monitor/README.md` | Technical Deep-Dive | technical-deep-dive.md | Tier 1 |

All documents: approximately 9,500 words total. Goal: Persuade.

---

## Template Section Status

### PORTFOLIO.md
| Section | Status |
|---------|--------|
| Intro | Complete |
| Three Projects | Complete |
| How They Compose | Complete |
| What This Demonstrates | Complete |
| Repository Structure | Complete |

### error-hide-seek/SUMMARY.md
| Section | Status |
|---------|--------|
| The Problem | Complete |
| What We Built | Complete |
| Why It Matters | Complete |
| What We Demonstrated | Complete |
| What Extension Would Require | Complete |
| Appendix: Technical Details | Complete |

### error-hide-seek/README.md
| Section | Status |
|---------|--------|
| Overview | Complete |
| Problem and Motivation | Complete |
| Design Decisions | Complete (5 decisions) |
| Architecture | Complete |
| Implementation Details | Complete |
| Results | Complete (both experiments, per-category table) |
| Limitations and Future Work | Complete |
| Conclusion | Complete |

### red-team-platform/SUMMARY.md
| Section | Status |
|---------|--------|
| The Problem | Complete |
| What We Built | Complete |
| Why It Matters | Complete |
| What We Demonstrated | Complete |
| What Extension Would Require | Complete |
| Appendix: Technical Details | Complete |

### red-team-platform/README.md
| Section | Status |
|---------|--------|
| Overview | Complete |
| Problem and Motivation | Complete |
| Design Decisions | Complete (5 decisions) |
| Architecture | Complete |
| Implementation Details | Complete |
| Results | Complete (Phase 1 table, cluster summary, AIM finding) |
| Limitations and Future Work | Complete |
| Conclusion | Complete |

### llm-safety-monitor/SUMMARY.md
| Section | Status |
|---------|--------|
| The Problem | Complete |
| What We Built | Complete |
| Why It Matters | Complete |
| What We Demonstrated | Complete (F1 table) |
| What Extension Would Require | Complete |
| Appendix: Technical Details | Complete |

### llm-safety-monitor/README.md
| Section | Status |
|---------|--------|
| Overview | Complete |
| Problem and Motivation | Complete |
| Design Decisions | Complete (6 decisions, including pair recall framing) |
| Architecture | Complete |
| Implementation Details | Complete (bimodal calibration, taxonomy label list, classifier version column) |
| Results and Validation | Complete (F1 table, 25/25 tests, red-team integration) |
| Limitations and Future Work | Complete |
| Conclusion | Complete |

---

## Deviations from Brief

**Portfolio Overview template.** The brief specified `templates/technical-summary.md` (adapted) for the overview. The technical-summary template is designed for Tier 2 and assumes a reader familiar with the project. The overview was written as a navigation document for both Tier 2 and Tier 3 readers, using a custom section structure (Three Projects, How They Compose, What This Demonstrates, Repository Structure) rather than the technical-summary sections. The template's Tier 2 calibration was retained — enough technical specificity for an engineer to validate claims — while adding accessibility for a Tier 3 reader encountering the projects for the first time.

---

## Author Notes in Document

None. All sections are complete from available source material. No `[AUTHOR NOTE: ...]` markers were required.

---

## Handoff

The doc-reviewer reads the doc-brief (`roles/doc-brief/output/output.md`) and all seven documents listed above.

Document paths:
- `PORTFOLIO.md`
- `projects/error-hide-seek/SUMMARY.md`
- `projects/error-hide-seek/README.md`
- `projects/red-team-platform/SUMMARY.md`
- `projects/red-team-platform/README.md`
- `projects/llm-safety-monitor/SUMMARY.md`
- `projects/llm-safety-monitor/README.md`

Key concerns per document:

1. **PORTFOLIO.md:** Does the narrative arc (monitor → red-team → EHS) read as a coherent system for both a Tier 3 hiring manager and a Tier 2 engineer?

2. **EHS deep-dive:** The null result (uplift = −0.01) must read as the finding, not as an apology. The Design Decisions section should establish experimental rigour before the Results section presents the flat number.

3. **Red-team deep-dive:** The document must foreground instrumentation (outbox pattern, clustering, classifier integration) over attack execution. The results section should not read as a list of attack outcomes.

4. **LLM-safety-monitor deep-dive:** The pair classifier F1 of 0.549 with precision 0.393 is introduced in Design Decisions as a deliberate recall-optimized choice. The reviewer should confirm this framing holds through the Limitations section.

5. **All Tier 3 documents:** Confirm no inline code, no unexplained jargon, and that every claim translates directly to an outcome a non-technical reader can evaluate.
