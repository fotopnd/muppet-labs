# Design Brief Output — moderation-stream `/stream` dashboard

**Role:** design-brief
**Sequence:** `new-project-full` (step 4)
**Date:** 2026-06-02

---

## Interface Context

**Application Dashboard**

This is a live operational monitoring view — five models running in parallel, emitting accuracy, latency, and throughput in real time. High data density, metric-heavy content, and a professional tool register. The user is a technical operator or hiring manager watching the system run, not a casual visitor. Application Dashboard applies without ambiguity.

---

## Primary Interaction

**Read and compare live per-model classification metrics as the stream runs.**

The user arrives to see how the five models are performing right now — not to act on data, configure anything, or navigate deeper. The dashboard is a read-only live display. The primary success state is: all five cards visible, all metrics updating, no confusion about which models are active vs pending.

---

## Key Visual Components

1. **`ModelMetricsCard`** — The primary data unit. One card per model slot. Two distinct states: `active` (full metrics panel) and `pending_weights` (placeholder with a clear "awaiting fine-tuned weights" message). Active state shows: model name, status badge, accuracy (or N/A), p50/p95 latency, throughput, total processed count. All numeric metrics render in monospace font per design_style.md data/code typography rule.

2. **Status Badge** — Inline within the card header. Two values: `Active` (emerald) and `Pending Weights` (slate/neutral). Semantic color is the only visual signal of model readiness — it must be unambiguous at a glance.

3. **Metrics Grid** — Five-card responsive layout. The layout must accommodate exactly 5 cards without orphan spacing issues: 1-col (mobile) → 2-col (md) → 3-col (xl), with the 5th card left-aligned in the final row rather than stretched.

4. **Stream Connection Indicator** — A header-level status line showing last-updated timestamp from `generated_at`. When the metrics API is unreachable the existing `ErrorMessage` component replaces the grid. The indicator communicates liveness without a dedicated "connected/disconnected" widget.

5. **Nav Link** — `/stream` entry added to the existing case-queue top navigation. Must sit alongside the existing links (Cases, Audit Log) without restructuring the nav component.

---

## Done Criteria

- All five model slots render on the `/stream` route, including Phase 2 slots in `pending_weights` state with a visible placeholder message (not a blank card or missing card).
- Status badge uses emerald for `active` and a neutral slate tone for `pending_weights`; no other colors used for this status signal.
- `accuracy` renders as `N/A` (not `0%`, not blank) when the value is `null`; all other numeric metrics render as `0` when zero.
- All numeric metric values (accuracy %, latency ms, throughput cps, total processed) use a monospace font, consistent with the design_style.md data/code typography rule.
- The metrics grid is responsive: 1-col below `md`, 2-col at `md`, 3-col at `xl`. The 5th card does not stretch to fill the row — it is left-aligned.
- The `generated_at` timestamp from the API response is visible and updates with each poll cycle (every 3 seconds).
- When the metrics API is unreachable, the grid is replaced by the `ErrorMessage` component with a clear message. No blank screen, no silent failure.
- The `/stream` nav link is present in the existing top navigation and navigates correctly to the dashboard route.
- No arbitrary pixel values or inline style overrides appear in any new component (`style=""`, `h-[Xpx]`, `w-[Xpx]` are all banned per design_style.md).

---

## Handoff

The `frontend-architect` reads this file alongside `roles/architect/output/output.md` and `resources/design_style.md`.

**Open decisions for frontend-architect to resolve:**
- Token mapping for the `pending_weights` slate badge — confirm the exact Tailwind token against the design_style.md neutral palette (Slate 200 boundary / Slate 900 text on light; Slate 700 / Slate 200 on dark).
- Whether `ModelMetricsCard` uses a shadcn/ui `Card` directly or a thin wrapper around it — given shadcn/ui is already installed, the default should be to use it.
- Loading skeleton vs spinner for the initial data fetch on `/stream` — the brief does not mandate either; frontend-architect decides based on the card layout.
- Exact placement of the `generated_at` timestamp — inside the dashboard header, or inside each card's footer. Frontend-architect decides; the done criterion only requires it to be visible and updating.
