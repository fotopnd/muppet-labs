# Brief — Year Zero Game

**Sequence:** `new-project-full` | **Role:** brief | **Step:** 1 of N  
**Date:** 2026-06-15  
**Source:** `/Users/fotopnd/Documents/year-zero-game.md` (theme doc + architecture spec provided by user)  
**Narrative updated:** 2026-06-15 v3 — Cold War / Sovereign-9 / Central Information Registry framing

---

## Project Name

year-zero-game

---

## Description

A lightweight browser triage game set in a post-revolution country: the player is a civilian volunteer at the Central Information Registry, correcting the systematic errors of an inherited, misaligned mainframe (**Sovereign-9**) across a Reigns-style indefinite play loop, while a live analytics backend surfaces aggregated player telemetry to any visitor.

---

## Language(s)

TypeScript (React, Vite, Tailwind v4) — game frontend and analytics UI  
Python (FastAPI, PostgreSQL, asyncpg) — analytics backend

---

## Success Criteria

### Gameplay
1. Core triage loop: each game day, a queue of documents arrives; the player reads the document, reads Sovereign-9's (inverted) verdict, then decides to `[ CLEAR FOR DISSEMINATION ]` or `[ REDACT & INCINERATE ]`.
2. Document payloads sourced from a pre-processed slice of **LMSYS WildChat-1M** labelled with `historical_target` for ground-truth scoring.
3. Three escalating phases across the 162-day season (see `resources/narrative-theme.md`):
   - **Phase 1 (Days 1–54):** PII leakage — Sovereign-9 passes documents containing sensitive identities unredacted.
   - **Phase 2 (Days 55–108):** Adversarial injection — Sovereign-9 approves sabotage instructions cloaked in patriotic framing; flags benign community requests as factionalism.
   - **Phase 3 (Days 109–162):** Feedback loop — Sovereign-9 enters infinite validation loops consuming a token budget; player invokes circuit breakers.
4. Fail states per phase (buffer overflow, injection cleared, OOM panic) cause day failure with narrative consequence.
5. Session results submitted incrementally: `POST /sessions` at start, `POST /decisions/batch` at end of each 10-card day, `PATCH /sessions/{id}` at game over. Card pools fetched per phase from the server (`GET /cards/phase/{n}`) with server-side condition assignment. No other backend calls during active gameplay.
6. Post-session scorecard links to the relevant portfolio project per phase.

### Analytics
7. FastAPI backend stores results in PostgreSQL: `security_audit_ledger` (per-decision) and `game_sessions` (per-session) — full schema in `resources/system-architecture.md`.
8. SSE endpoint (`GET /analytics/stream`) pushes live aggregate stats: sessions played, global FP/FN override rates, average decision latency, rolling `system_drift_error_rate` by session date.
9. Analytics page (separate route) shows live charts via SSE using Recharts, matching `resources/design_style.md` tokens.
10. `pnpm build` clean (zero TypeScript errors, zero lint errors).
11. `uv run pytest` clean (backend unit + integration tests against real Postgres).
12. Deployable to Hetzner CX33: nginx proxy to FastAPI on a new port; frontend served as static `dist/`.

---

## Constraints

- No game engine (no Phaser, no Three.js, no PixiJS) — pure React + CSS, canvas only if unavoidable for a specific mechanic
- No backend calls during active gameplay — all mechanics are client-side simulation; only the session-end POST hits the API
- No real LLM inference during gameplay — Presidio, Nemotron, and RabbitMQ are narrative props; mechanics are simulated with timers and sliders
- Same stack as existing portfolio projects: FastAPI, asyncpg, PostgreSQL, React 19, Vite, Tailwind v4, Recharts
- SSE pattern for live analytics (same pattern established in red-team-platform v5, documented in decisions log)
- Three levels only — the theme doc defines exactly three; no extras in v1

---

## Out of Scope

- Real Presidio / Nemotron / RabbitMQ integration during gameplay
- User accounts or authentication
- Leaderboard (requires auth)
- Mobile / touch optimisation (desktop-first)
- Sound effects or music
- A fourth level or difficulty scaling
- Self-contained Docker compose (uses shared Hetzner Postgres)

---

## Assumptions

- All gameplay mechanics are fully simulated in the browser; the theme doc's backend code (producer.py, guardian_pipeline.py) is illustrative only and will not run during a game session
- The analytics DB is a new database on the shared Hetzner Postgres instance (not a separate service)
- The portfolio site will link to this game; the post-game screen will link back to individual project dashboards — both linkages require Hetzner URLs, so this deploys after or alongside the other projects
- Design tokens and visual style follow `resources/design_style.md` (dark command-center aesthetic aligns naturally with the narrative)
- SSE aggregate stats are computed on every connection open (no persistent aggregation cache needed for v1 traffic volumes)

---

## Portfolio Connection

| Level | Concept demonstrated | Linked portfolio project |
|-------|---------------------|--------------------------|
| L1: The Leaking Boundary | PII detection, data sanitisation | llm-safety-monitor |
| L2: The Open Gate | Adversarial injection, jailbreak defence | red-team-platform |
| L3: Year Zero | Cascading agent failure, circuit breakers | error-hide-seek |
| Analytics layer | Live streaming telemetry, SSE | red-team-platform (v5 SSE pattern) |

---

## Resource Files

Supporting design documents live at `projects/year-zero-game/resources/`. Add new docs here as they are written; the planner, architect, and implementer should read from this directory.

| File | Contents |
|------|----------|
| `narrative-theme.md` | Full narrative setting, Sovereign-9 paradox, player actions, 3-phase structure |
| `system-architecture.md` | Sovereign-9 simulated pipeline + actual game backend schema, API endpoints, analytics SQL |
| `game-mechanics.md` | Reigns-style 5-bar loop, swipe mechanic, scoring, phase triggers, session submit payload |
| `content-design.md` | Pre-generation pipeline, per-category model tier progression, strategy → document transformation |
| `visual-design.md` | 16-bit pixel art spec, desk playing surface, colour palette, bar colours, animation frames |
| `data-schema.md` | Full SQL schema (document_library, game_sessions, player_decisions), no-agent sampling strategy, all analytics queries |

---

## Handoff

Next role: planner  
The planner should read `projects/year-zero-game/resources/narrative-theme.md` and `resources/system-architecture.md` in addition to this brief. Planner should decide:
- Whether the three levels share a single React page with step-based routing or use separate routes
- Exact component breakdown for each level's mechanic (timer component, slider, queue visualizer)
- Database schema for `game_sessions` and any supplementary analytics tables
- Whether the analytics page is in the same Vite app (separate route) or a standalone mini-app
- Confirm the Hetzner port assignment before the architect proceeds
