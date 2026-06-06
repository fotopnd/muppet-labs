# Design Brief Output — moderation-dashboard

**Role:** design-brief
**Sequence:** `new-project-full` (step 4)
**Date:** 2026-06-03

---

## Interface Context

**Application Dashboard.**

This is a high-density operational monitoring tool for an ML inference pipeline — multiple panels of live model metrics, event stream data, anomaly signals, and an escalation queue. It has no marketing intent and no documentation purpose. It fits the Application Dashboard context exactly: multi-pane layout, monospace metric display, sticky navigation, real-time data updates, operational register throughout.

---

## Primary Interaction

**Compare model performance across the two routing strategies.**

The user arrives to understand whether the models attached to the dashboard are performing differently — both on their round-robin production traffic (Model Performance panel) and on identical events in the shadow evaluation (Model Comparison panel). All other panels (Stream Monitor, Human Review, Analytics) are supporting context; the head-to-head model comparison is the core product story and the reason the dashboard exists.

---

## Key Visual Components

1. **ModelCard** — the primary display unit. Shows one model's name, status badge (`active` or `pending_weights`), F1, latency p50/p95, and throughput. Used in both Model Performance (production group metrics) and Model Comparison (shadow group metrics). Must render a visually distinct greyed state when `status = pending_weights` with no metric values shown and an "Awaiting checkpoint" label.

2. **MetricSparkline** — a compact recharts `LineChart` embedded inside each active `ModelCard`. Single line, no legend, monospace axis labels, 30-point rolling history. Shows F1 trend over time. Visible at all times on active cards (not on hover or expand).

3. **PanelTabBar** — tab navigation across the top of the dashboard with five tabs: Stream Monitor | Model Performance | Model Comparison | Human Review | Analytics. Active tab has a primary-accent bottom border (`border-b-2 border-primary`). Tab switching is the only top-level navigation gesture in the UI.

4. **AnomalyFeedItem** — a single row in the Stream Monitor anomaly feed. Displays: signal name (e.g., `event_volume`), Z-score as a monospace number with an amber badge if Z > 3, window timestamp in relative format (e.g., "4 min ago"). Read-only, no interaction.

5. **EscalationCaseRow** — a single row in the Human Review escalation queue. Displays: truncated event content (first 80 chars), category badge, escalation reason (`model_disagreement` or `low_confidence`), and a link icon that opens the case in case-queue. No decision controls — link-out only.

---

## Done Criteria

1. All five panels are reachable via `PanelTabBar`; the active tab has a visible primary-accent bottom border; inactive tabs have no underline.
2. `ModelCard` renders correctly in both states: `active` cards show computed F1, latency p50/p95, throughput, and a `MetricSparkline`; `pending_weights` cards are visually desaturated (reduced opacity or `text-muted-foreground`), show "Awaiting checkpoint" in place of metrics, and show no sparkline.
3. Every panel shows a skeleton loading state (shadcn `Skeleton` component) while its data fetch is in-flight — not a blank panel, not a spinner in the center of the screen.
4. Every panel independently shows a named error state when its API call fails (e.g., "Model metrics unavailable — retrying"); sibling panels must remain fully functional when one panel errors.
5. Stream Monitor displays: event rate as a number with unit label ("events / sec"), a bar chart with all 7 categories (6 Jigsaw categories + "clean") each labelled, and the anomaly feed as a scrollable list — all three sections visible without scrolling on a 1280px viewport.
6. Model Comparison panel shows a numeric F1 delta between models — at minimum a table or card set where each model pair's accuracy difference is a visible number, not only a chart.
7. Human Review panel shows a count badge reflecting the number of pending escalated cases; when case-queue is unreachable the panel displays an explicit "Case queue unavailable" message with a visible retry state — it does not render an empty list silently.
8. Analytics panel displays "No data yet — run `make dbt-refresh` to populate" with an explanatory subline when all three dbt mart tables are empty; no broken empty chart axes are shown.
9. All metric values (F1, latency, throughput, Z-score, event rate) render in the monospace font defined in the design token; category labels, model names, and panel headings render in the primary sans-serif.
10. No arbitrary pixel values appear in any `className` string (no `h-[13px]`, `w-[342px]`, or `style=""`); all spacing uses Tailwind scale tokens.

---

## Handoff

The `frontend-architect` reads this file alongside `roles/architect/output/output.md` and `resources/design_style.md`.

**Open decisions for frontend-architect to resolve:**

- **Model Performance vs Model Comparison layout:** These are separate tabs in the brief. The frontend-architect should decide whether Model Comparison is truly a second tab or a toggle/sub-view within Model Performance (e.g., a "Compare" button that shifts the card grid into a diff view). Either is valid — lock one before specifying components.
- **ModelCard grid layout:** Decide the card grid per panel — 3-up row (Phase 1) vs 5-up row (Phase 2) vs wrapping grid. Must handle both Phase 1 (3 active cards) and Phase 2 (5 active cards) without layout reflow.
- **Stream Monitor hero layout:** Decide whether Stream Monitor gets a wider or full-width layout as the landing panel, or shares the same container width as other panels.
- **MetricSparkline data source:** The sparkline shows 30-point rolling F1 history. The API currently returns a single current-window F1, not a time series. Frontend-architect must decide whether the rolling history is maintained in React state (TanStack Query refetch accumulates points client-side) or served from a new API endpoint. Client-side accumulation is simpler; an endpoint is more correct after page refresh.
