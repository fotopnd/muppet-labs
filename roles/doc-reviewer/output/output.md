# Doc-Reviewer Output — Anthropic Safeguards Portfolio Writeups

## What Was Edited

**PORTFOLIO.md:** No changes required. Clean on first read.

**error-hide-seek/SUMMARY.md:** One fix. Line 28: em-dash changed to colon in "demonstrates experimental rigour — honest null results..." Voice rule enforcement.

**error-hide-seek/README.md:** Six em-dash violations fixed throughout. Each changed to the appropriate alternative (comma + participial phrase, comma + "meaning", colon, "and", parenthetical). No structural or content changes. All key messages present.

**red-team-platform/SUMMARY.md:** Two fixes. Em-dashes around list of provenance fields changed to parenthetical. Semicolon in latency sentence changed to ", while".

**red-team-platform/README.md:** Two fixes. Em-dashes around provenance list changed to parenthetical. Em-dash + semicolon in the latency gap sentence changed to colon + new sentence.

**llm-safety-monitor/SUMMARY.md:** Four fixes.
- Opening sentence of The Problem restructured to remove em-dash.
- "PostgreSQL with full classification provenance" changed to "PostgreSQL with a full record of each classification result" — "provenance" is jargon for the Tier 3 audience.
- F1 definition added before the classifier table: "F1 score is a standard accuracy measure that combines how often a flag is correct (precision) with how often a real issue is caught (recall)." The pair classifier explanation was also simplified for the Tier 3 audience: "tuned to catch as many harmful interactions as possible (recall 0.910), accepting more false flags in return" replaces the precision/recall number pair without context.
- Three semicolons in the What Extension Would Require bullets changed to periods or commas.

**llm-safety-monitor/README.md:** One fix. Two semicolons in the conclusion sentence changed to periods: "The pair classifier is intentionally recall-heavy. The taxonomy classifier provides harm-category specificity. The prompt classifier provides intent context."

---

## Author Flags

None — document is complete.

---

## Verdict

READY — all seven documents are publication quality. No `[AUTHOR: ...]` markers. All key messages present in all documents. Voice rules enforced throughout. Tier 3 documents (all three SUMMARY files and PORTFOLIO.md) contain no inline code in body sections and no unexplained jargon. Tier 1 documents (all three README files) contain concrete design decisions backed by specific numbers, code paths, or observable behaviours.

---

## Handoff

No further action required. Documents are at:

- `PORTFOLIO.md`
- `projects/error-hide-seek/SUMMARY.md`
- `projects/error-hide-seek/README.md`
- `projects/red-team-platform/SUMMARY.md`
- `projects/red-team-platform/README.md`
- `projects/llm-safety-monitor/SUMMARY.md`
- `projects/llm-safety-monitor/README.md`
