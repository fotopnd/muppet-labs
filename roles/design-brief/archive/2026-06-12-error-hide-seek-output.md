# Design Brief Output — error-hide-seek

**Role:** design-brief
**Sequence:** `new-project-full` (step 4)
**Date:** 2026-06-07

---

## Interface Context

**Application Dashboard.**

error-hide-seek is a single-user research tool — a researcher runs experiments, reviews abstracts one-by-one, and reads detection rates. There is no marketing intent and no documentation purpose. The review page is task-focused (action surface for flagging errors); the results page is data-dense (metric table with computed uplift). Both pages call for the Application Dashboard register: clean structure, monospace for metrics, operational clarity over decoration.

---

## Primary Interaction

**Read an altered AI safety abstract (with optional blue team annotation highlights), flag suspected planted errors by selecting text, and submit detections.**

The ReviewPage is where the experiment runs. Everything else — experiment setup, results — is secondary. A user arrives at `/review/:sessionId`, reads the abstract, uses the Selection API to highlight and flag suspicious text, and submits. The ResultsPage is a read-out, not an action surface.

---

## Key Visual Components

1. **`AnnotatedAbstract`** — the abstract text rendered with inline highlighted `<mark>` spans for each blue team annotation. Highlight colour varies by confidence: amber for high, yellow-100 for medium, slate-100 for low. Hovering a span shows a tooltip with the confidence badge and reason text. Absent for `unaided` sessions (abstract renders as plain text). The most visually distinctive component in the interface.

2. **`SelectionFloater`** — a floating button that appears near the user's text selection when the selection is ≥15 characters. Label: "Flag selection". Clicking appends `{text_excerpt, note: ""}` to the detection list and clears the browser selection. Invisible and non-interactive below the 15-character threshold.

3. **`DetectionList`** — the staged list of flagged excerpts below the abstract. Each item: a monospace excerpt chip (truncated to 60 chars), an optional note `<input>`, and a remove ×  button. Empty state: "No errors flagged yet — select text above to flag." Submit button at the bottom, disabled while mutation is in-flight. An empty detection list is valid (the human found nothing).

4. **`UpliftHero`** — the headline metric on ResultsPage. Large numeric display: `+X.X%` (emerald) when uplift > 0, `-X.X%` (destructive/red) when uplift < 0, "Results incomplete" (muted, smaller) when any required condition is still in progress.

5. **`ConditionResultsTable`** — a three-column table (Unaided / Agent Only / Human + Agent). Rows: True Positive Rate, False Positive Rate, Sessions Complete. The Human + Agent TPR cell is background-highlighted — emerald-50 if uplift > 0, rose-50 if negative, default if null. All numeric values render in monospace. Below the main table: a per-category breakdown table (rows = error categories, columns = conditions, cells = TPR % or "—" if condition incomplete).

---

## Done Criteria

1. `AnnotatedAbstract` renders: highlighted spans have visually distinct background (amber, yellow-100, or slate-100 by confidence level); hovering a span reveals a tooltip containing a confidence badge and one-sentence reason; plain text renders with no highlights for `unaided` sessions.

2. `SelectionFloater` appears when the user highlights ≥15 characters of abstract text; does **not** appear for selections shorter than 15 characters. Clicking "Flag selection" adds the excerpt to the detection list and the selection is cleared.

3. `DetectionList` renders: each detection item shows a monospace truncated excerpt, an optional note field, and a remove button; the empty state message is shown (not an empty container) when no detections are staged; the submit button is disabled while the review mutation is in-flight.

4. ReviewPage shows a "Session already completed" banner (not the detection form) when `session.status === 'completed'`. The abstract and any annotations remain visible in read-only form.

5. `UpliftHero` renders the correct semantic state: emerald text for positive uplift, destructive/red for negative, muted "Results incomplete" text when `uplift === null`. The numeric format is always `+X.X%` or `-X.X%` (one decimal, sign explicit).

6. `ConditionResultsTable` renders: three columns are present regardless of condition completeness; the Human + Agent TPR cell has an emerald-50 background when uplift > 0 and rose-50 when negative; incomplete conditions show "—" (not 0% or blank) in all cells; all percentage values are in the monospace font.

7. The per-category breakdown table below `ConditionResultsTable` renders: one row per error category present in the experiment, three columns (one per condition), each cell showing the category TPR % or "—". The table has a visible header row with condition labels.

8. Both pages show named loading skeletons while their primary API call is in-flight, and a named error message (e.g. "Session unavailable — check API") on failure. Error state does not render partial data.

9. No arbitrary pixel values appear in any `className` string (`h-[13px]`, `w-[342px]`, `style=""` are all banned). All spacing uses Tailwind scale tokens.

---

## Handoff

The `frontend-architect` reads this file alongside `roles/architect/output/output.md` and `resources/design_style.md`.

**Open decisions for frontend-architect to resolve:**

- **`SelectionFloater` positioning strategy:** The floating "Flag selection" button must appear near the user's text selection. Two options: (a) use `window.getSelection().getRangeAt(0).getBoundingClientRect()` to position with `position: fixed`, rendered via a React portal; (b) position relative to the abstract container using a ref. Option (a) is more accurate across scroll positions; (b) is simpler. Frontend-architect decides.

- **Overlapping annotation highlights:** If two `AnnotatedAbstract` annotations cover overlapping text ranges, the substring-search segmentation algorithm may produce nested or crossed highlights. Frontend-architect should specify the tiebreaker — proposed: first annotation wins (process in index order, skip annotations whose text is already inside a prior highlighted segment).

- **ResultsPage polling:** Should `useResults` poll at an interval while any condition is incomplete? This would let the page update live as sessions are completed without a manual refresh. Proposed: poll every 30s if `uplift === null` (conditions incomplete), stop polling once all conditions complete. Frontend-architect confirms or drops.

- **Category breakdown table placement:** The per-category breakdown could be a separate collapsible section below `ConditionResultsTable`, or always-visible. Frontend-architect decides based on how many rows are typically expected (5 error categories max — always-visible is cleaner).
