# Design Brief Output — llm-safety-monitor (UI Redesign)

**Role:** design-brief
**Sequence:** `add-feature` (tab redesign — post-implementer amendment)
**Date:** 2026-06-06

---

## Interface Context

**Application Dashboard.**

This is a real-time LLM safety monitoring tool — three purpose-trained classifiers processing a
continuous replay of LLM interaction datasets, surfacing escalations, calibration state, and
harm taxonomy trends to a technical operator. The use is entirely operational: no marketing
intent, no documentation purpose. Application Dashboard context applies: high data density,
monospace metric display, sticky tab navigation, real-time polling throughout.

---

## Primary Interaction

**Understand what the classifiers are catching right now and act on escalated cases.**

The user arrives to answer two questions in sequence: (1) Is the live stream producing flagged
events at the expected rate, and what are the three classifiers saying about them? (2) Which
escalated events need a human decision? The StreamMonitor and HumanReview panels are the
operational core. ModelPerformance and Taxonomy Trends are the diagnostic layer — a user who
sees an unexpected F1 drop or a taxonomy spike navigates there to investigate.

---

## Key Visual Components

1. **EventFeedItem** — the content unit for the StreamMonitor tab. Each item displays:
   prompt text (truncated), `SourceBadge`, `VerdictRow` (three classifier verdicts inline),
   and `EscalationReasonBadge` (only rendered when `escalation_reason` is non-null). Items
   are stacked vertically; the feed scrolls. No interaction — read-only.

2. **VerdictRow** — a 3-column inline display shared by `EventFeedItem` and `EscalationCard`.
   Column 1: pair classifier verdict (Safe/Unsafe badge). Column 2: prompt detector verdict
   (Benign/Adversarial badge). Column 3: taxonomy classifier output (one chip per active
   HarmCategory, or muted "none" text when `taxonomy_labels` is empty).

3. **ModelPerformanceCard** — one card per classifier. Displays F1, precision, recall as
   monospace numeric values sourced from `GET /metrics`. Embeds a recharts `LineChart`
   showing the F1 timeseries from `GET /metrics/timeseries?bucket_minutes=60`. The chart
   renders with the model name as its heading; time on x-axis, F1 (0–1) on y-axis.

4. **TaxonomyTrendChart** — recharts chart for the Taxonomy Trends tab. X-axis: time
   bucket timestamps from `GET /metrics/taxonomy/timeseries?bucket_minutes=60`. Y-axis:
   event count. One series per harm category present in the response. Renders a
   "No taxonomy data yet" placeholder when the dataset is empty.

5. **EscalationCard** — the content unit for the HumanReview tab. Displays: prompt text
   (truncated), response text (truncated, or "(no response)"), `VerdictRow`, and
   `EscalationReasonBadge`. Includes three action buttons: **Approve**, **Dismiss**,
   **Escalate** — each POSTs `{"decision": "approve"|"dismiss"|"escalate"}` to
   `POST /cases/{id}/decide`. Buttons are disabled while a submission is in-flight.

---

## Done Criteria

1. `PanelTabBar` has exactly 4 tabs: **Stream Monitor | Model Performance | Taxonomy Trends |
   Human Review**. Active tab has a visible primary-accent bottom border (`border-b-2
   border-primary`); inactive tabs have no underline or background accent.

2. StreamMonitor renders `EventFeedItem` entries correctly: prompt text is visibly truncated,
   `SourceBadge` renders with a distinct color for each of the 5 `SourceDataset` values
   (hh-rlhf=blue, wildguard=purple, advbench=red, jailbreakbench=orange, live=green),
   `VerdictRow` renders all three classifier verdicts in separate columns, and
   `EscalationReasonBadge` is absent (not an empty element) when `escalation_reason` is null.

3. `VerdictRow` renders correctly across all verdict states: pair=Safe (neutral badge),
   pair=Unsafe (red/destructive badge), taxonomy with 0 active categories ("none" in muted
   text), taxonomy with ≥1 active categories (one chip per category).

4. ModelPerformance renders one `ModelPerformanceCard` per classifier. Each card shows
   F1/precision/recall as numeric values in the monospace font. The embedded `LineChart`
   renders with ≥1 data point and shows a "No timeseries data" placeholder when the
   timeseries response returns an empty bins array.

5. Taxonomy Trends renders `TaxonomyTrendChart` with: time buckets on the x-axis, counts on
   the y-axis, and one rendered series per harm category present in the response data.
   When the endpoint returns empty data, the tab shows "No taxonomy data yet" — no broken
   empty chart axes.

6. HumanReview renders one `EscalationCard` per pending case. Approve/Dismiss/Escalate
   buttons are visible and enabled when idle; disabled while a submission is in-flight. After
   a successful decision, the card is removed from the view. When the queue is empty, the
   panel shows an explicit "No pending cases" message — not an empty list.

7. Every panel shows a `Skeleton` loading state while its API call is in-flight. Each panel
   independently renders a named error state (e.g. "Stream unavailable — retrying") when its
   call fails, without affecting sibling panels.

8. All metric values (F1, precision, recall, confidence) render in the monospace font. All
   category labels, model names, and headings render in the primary sans-serif.

9. No arbitrary pixel values appear in any `className` string (no `h-[13px]`, `w-[342px]`,
   no `style=""`); all spacing uses Tailwind scale tokens.

---

## Handoff

The `frontend-architect` reads this file alongside `roles/architect/output/output.md` and
`resources/design_style.md`.

**Open decisions for frontend-architect to resolve:**

- **TaxonomyTrendChart chart type:** With up to 13 harm categories (most sparse), the
  architect should choose between grouped bar, stacked bar, and multi-line. Grouped bar is
  readable for few active categories; stacked bar communicates total volume; multi-line
  handles sparse data cleanly. Decide before specifying the component.

- **`ModelPerformanceCard` timeseries bucket:** The `/metrics/timeseries` endpoint accepts
  `bucket_minutes` as a query param. Decide whether this is fixed at 60 in the hook
  (simple, no UI control) or configurable via a UI dropdown (adds a filter control to the
  ModelPerformance tab). If configurable, specify the dropdown component and values.

- **EscalationCard list management:** After a decision is submitted, decide between
  optimistic removal (remove immediately on button click, rollback on error) vs
  refetch-on-success (re-query the queue; card disappears when queue response updates).
  Optimistic is snappier; refetch is simpler and safer.

- **HumanReview pagination:** If the escalation queue grows large, decide between paginated
  list (a fixed page size with prev/next controls) or scroll-based rendering. Pagination
  is easier to implement and avoids DOM cost; frontend-architect to choose based on expected
  queue depth.

- **Tabs dropped from original design:** `Calibration` and `Model Comparison` tabs are
  explicitly removed in this redesign. Frontend-architect should not re-introduce these
  or reference their components in the new spec.
