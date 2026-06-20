# CONTEXT.md — Gridiron Project

> Load this file at the start of every gridiron session.
> It tells you what has been decided, what is in-flight, and what to do next.
> Update the Active Work section after each session.

---

## What This Project Is

24/7 autonomous college football simulation engine. Fictional universe. No user interaction in v1.
Publishes live play-by-play events, rolling stats, and completed game replays to a public web frontend.
Portfolio piece demonstrating live SSE streaming, event-driven analytics, and replay architecture.

---

## Privacy Boundary

| Path | Status |
|------|--------|
| `gridiron/engine/` | PRIVATE — never public |
| `gridiron/api/` | Shareable |
| `web/` | Shareable |
| `resources/engine-constants.md` | PRIVATE — do not quote in public write-ups |

---

## Stack

- Backend: Python / FastAPI / SQLAlchemy async / PostgreSQL
- Frontend: React 19 / TypeScript / Tailwind v4 / Vite
- Streaming: SSE (in-process asyncio queue, single uvicorn worker)
- Ports: backend 8006 · DB 5438 · frontend dev 5177
- Deploy: Hetzner CX23 (systemd) + Cloudflare Pages

---

## Sequence Position

| Step | Role | Status |
|------|------|--------|
| 1 | brief | ✅ done — `roles/brief/output/output.md` (2026-06-20) |
| 2 | planner | ⏳ next |
| 3 | architect | — |
| 4 | design-brief | — |
| 5 | frontend-architect | — |
| 6a | implementer (backend) | — |
| 6b | implementer (frontend) | — |
| 7 | reviewer | — |

---

## Locked Decisions

### Universe
- Fictional universe — legal remapping of real college football landscape (teams, stadiums relocated to nearby cities)
- 130 teams / 5 Broadcast Conglomerates / 26 teams per conglomerate / 13 Tier 1 + 13 Tier 2
- Promotion/relegation: bottom 2 Tier 1 ↔ top 2 Tier 2 per conglomerate each season ("The Boardroom Swap")
- Roster cap: 105 players per program, hard limit
- Named players, coaches, boosters — generated procedurally; 4-year graduation clock
- Elo rating system drives all standings, seeding, and tiebreaking
- Tiebreaker hierarchy: Head-to-Head → Elo → Point Differential

### Season
- 26-week regular season; 60 games/week (6 per tier per conglomerate); 1 bye/week per tier
- Weeks 25–26: "Rivalry Window / Exhibition Shield" — cross-tier, full Elo weight, no exhibition buffer
- Each program: 24 games played + 2 byes over the regular season
- 32-team postseason tournament: 5 single-elimination rounds over 5 weeks (in scope for v1)
- Conference Championship Games precede bracket: Tier 1 champion vs. Tier 2 champion per conglomerate
- Seeding: Elo-based 1–32; cross-network matchups prioritised for broadcast ratings
- Tier 2 guaranteed bracket pathway: top 2 Tier 2 champions by Elo get automatic at-large bids
- Ultimate Ascent Clause: Tier 2 at-large winner → immediate Tier 1 promotion; triggers 3-team relegation that season
- Season reset: hard reset (records/standings); soft reset (player progression/archive written)

### Simulation
- Game computes in 5–10 seconds; streams to client time-dilated over 10 real minutes
- Engine throughput: full 60-game weekly slate processed simultaneously in ~30 seconds
- 120–150 plays per game
- Play types: KICKOFF, PUNT, FIELD_GOAL_ATTEMPT, RUSH, PASS_COMPLETE, PASS_INCOMPLETE, PASS_DEFLECTION, TOUCHDOWN, SAFETY, PAT_CONVERSION, TWO_POINT_CONVERSION, TURNOVER_INTERCEPTION, TURNOVER_FUMBLE, SACK, TACKLE_FOR_LOSS, PENALTY
- "Primetime Drama Multiplier": +15% variance in critical events during Rivalry Window and postseason only
- Out of scope v1: injuries, weather, coaching decisions, off-field discipline

### Data
- Every play written to `play_log` table (mandatory for per-player stat aggregation)
- Full box scores, end-of-week standings, Elo ratings persisted
- Replay stored as complete chronological event stream with JSON state packets (play state + description string + stat deltas + 2D spatial coordinates)
- Replay modes: All Plays / Key Plays Only / Drive Chart Summary

### Frontend (confirmed pages)
- Dashboard / Hub (global 130-team view, live ticker, weekly schedule)
- Conglomerate Hubs ×5 (Tier 1/Tier 2 standings, revenue metrics)
- Team Profile View (roster, Elo chart, trophy case, schedule)
- Gamecast Central (live feed + replay viewer in one view)
- Visual: dark mode, financial dashboard × broadcast data aesthetic, monospaced data tables, high density

### Engine privacy
- Engine logic is private; API + frontend are portfolio-shareable

---

## ✅ Resolved: Simulation Execution Pattern

**Decision: simulation runs in a thread pool executor, not inline in the asyncio event loop.**

The weekly slate (~30s CPU burst) is pure synchronous Python — no I/O. Running it inline would freeze the entire API and all SSE connections for 30 seconds every slate cycle. Fix:

```python
await asyncio.get_event_loop().run_in_executor(None, run_simulation_slate)
```

Engine code stays synchronous, clean, and testable. The executor call is the only async boundary. This must be the invocation pattern everywhere the engine is called from the simulation loop.

---

## ✅ Resolved: Stats Storage Strategy

**Decision: two-table split. `play_log` stores narrative + primary credits. `player_game_stats` stores aggregated totals.**

Section 5.2 stats at per-play × 22-player granularity = ~6M rows/season. At ~200 bytes each, 40 GB SSD fills within 2–3 seasons.

| Table | Contents | Written when |
|-------|----------|-------------|
| `play_log` | Full event JSON (play state, description string, spatial coords, primary stat credits) | Every play, during simulation |
| `player_game_stats` | Aggregated season/game totals per player per position group | Once, at game end |

Replay and live feed read from `play_log`. Leaderboards, standings, and team profiles query `player_game_stats`. Reduces storage by ~10× with no loss of user-facing capability.

---

## ✅ Resolved: Streaming Architecture

**Decision: SSE with per-game queues. No WebSocket.**

Design doc section 6.2 said "WebSocket" meaning real-time server push — the intent is preserved, the protocol is SSE.

Rationale: v1 is unidirectional (server → client only; no user interaction). WebSocket adds bidirectionality and binary framing that v1 does not use. SSE handles this natively, works through Cloudflare proxying without config, has built-in browser reconnection, and requires no new dependencies.

Year-zero pattern extended minimally:

| Channel | Endpoint | Queue structure | Pattern |
|---------|----------|----------------|---------|
| Dashboard global ticker | `/stream/ticker` | `app.state.ticker_queues: list[Queue]` | year-zero identical |
| Per-game live feed | `/games/{game_id}/stream` | `app.state.game_queues: dict[int, list[Queue]]` | per-game fan-out |

Simulation loop calls `broadcast_play(game_id, event)` → fans out to `game_queues[game_id]` only.
Single uvicorn worker constraint maintained (in-process state).

---

## Active Work

_Update this section at the end of each session._

**Last session:** 2026-06-20 — scaffold created, brief written, setup files created; design-doc.md filled by user
**Blocked on:** SSE vs. WebSocket decision (planner must resolve); team/conglomerate name list (TBD); secret player attributes (TBD)
**Next action:** Resolve SSE/WebSocket → run planner role

---

## Resource Map

| File | Purpose | Read by |
|------|---------|---------|
| `CONTEXT.md` | Session anchor | All roles, every session |
| `writing-voice.md` | Tone and terminology | author, doc-reviewer, frontend-architect |
| `design-doc.md` | Universe + mechanics + UX vision | planner, architect, design-brief, implementer |
| `system-architecture.md` | Technical decisions (created by architect) | implementer, reviewer |
| `data-schema.md` | DB tables and relationships (created by architect) | implementer, sim-tuner |
| `engine-constants.md` | Balance parameters (PRIVATE) | sim-tuner only |
