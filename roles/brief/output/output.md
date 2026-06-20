# Brief — gridiron: College Football Simulation Engine

**Role:** brief
**Sequence:** new-project-full
**Date:** 2026-06-20

---

## Project Name
`gridiron`

## Description
A 24/7 autonomous college football simulation engine that publishes live play-by-play events, rolling stats, and completed game replays to a public web frontend — with no user interaction in v1.

## Language(s)
Python (simulation engine + FastAPI backend) + TypeScript (React frontend) — mixed, full-stack. Same stack as year-zero-game.

## Success Criteria

v1 is done when:
1. The simulation loop runs continuously via systemd on Hetzner with no manual restarts — games start and finish on their own schedule, 24/7
2. A live play-by-play SSE stream is available: clients connect and receive events as they are generated (touchdown, turnover, field goal, quarter end, etc.)
3. A standings/stats page shows cumulative season statistics updated after each game (team records, points for/against, top performers)
4. A game replay viewer allows browsing any completed game's play sequence with timestamps
5. The analytics page demonstrates live event ingestion in a way that reads as a portfolio piece — real-time update counts, event breakdown charts, team performance over time
6. Deployed on existing Hetzner box: FastAPI backend (port 8006), Postgres DB (port 5438), Cloudflare Pages frontend

## Constraints

- **Infrastructure:** Hetzner CX23 (shared 2 vCPU / 4 GB RAM). No GPU, no LLM inference during gameplay. Pure Python stat math + DB writes.
- **Same deployment pattern as year-zero:** systemd service, uvicorn, Postgres, wrangler for frontend.
- **Private repo:** Simulation engine, game logic, team/player generation, and scoring constants must never be pushed to a public GitHub repo. The public share boundary is analytics page code and replay viewer code only.
- **Port allocation:** frontend 5177, backend 8006, DB 5438 — next available in workspace map.
- **No user interaction in v1:** no betting, voting, team picking, or account system.
- **No external data dependencies:** teams, rosters, and stadiums are fictional — no licensing issues, no API dependencies.

## Out of Scope (v1)

- User accounts, authentication, or session tracking
- Live LLM-generated commentary or play descriptions (plain structured event types only)
- Betting or prediction mechanics
- Playoff bracket / championship structure (regular season only)
- Public GitHub exposure of game engine or simulation constants
- Mobile-optimised UI (desktop-first is fine for v1)
- Historical real-world team data or licensing

## Key Design Decisions (capture now, confirm in planner)

1. **Fictional universe** — teams, conferences, players, and stadiums are invented. Blaseball-style: strange names, emergent lore potential, no IP risk. Assumption: user confirms this over realistic NCAA data.
2. **Simulation cadence** — one game runs every N minutes (e.g. 20 min real-time = 1 game). Multiple games can run in parallel per "week". Exact cadence: planner decision.
3. **Season structure** — a regular season of K weeks with G games per week, looping back to a new season when complete. No playoffs in v1.
4. **Event granularity** — plays are discrete typed events (rush, pass_complete, pass_incomplete, sack, touchdown, field_goal, punt, turnover, quarter_end, game_end). Stats computed from events, not stored separately.
5. **SSE fan-out** — same pattern as year-zero analytics stream: in-process asyncio queue per subscriber, broadcast from simulation loop. Single uvicorn worker required (same constraint as year-zero).
6. **Public/private split** — the simulation engine (`gridiron/engine/`) is never committed to a public repo. The frontend (`web/`) and the API router layer (`gridiron/api/`) may be shared as portfolio sample code — they demonstrate the live analytics pattern without revealing the game mechanics.

## Assumptions

- User confirms fictional universe (vs. real-world NCAA data)
- Simulation constants (scoring probabilities, play distributions) are the "secret sauce" — not shared publicly even if the rest of the codebase is
- The project lives at `projects/gridiron/` in the muppet-labs monorepo but is excluded from any public mirror
- Portfolio value is primarily in the frontend: live SSE consumption, event-driven charts, replay timeline — not the engine itself
- Hetzner memory budget: year-zero + 3 others already use ~2 GB baseline; gridiron adds ~300 MB (uvicorn + Postgres idle); stays within 4 GB

## Handoff

**Next role:** planner

Planner reads this file and resolves:
1. Season/week/game cadence — how many games per week, how long per game, how many weeks per season?
2. Team and player count — how many teams, how many named players per roster, how much does roster size affect DB schema complexity?
3. Event schema — what fields does a play event carry? (team, player, event_type, yards_gained, quarter, game_clock, score_home, score_away)
4. Stats aggregation strategy — computed at query time (like year-zero analytics) or materialised after each game?
5. Replay storage — store full event log per game in Postgres (simple) vs. separate event log table (queryable)?
6. Frontend page structure — how many pages/tabs: Live Feed, Standings, Game Replay, Season Stats?
7. Confirm port allocation (8006 / 5438 / 5177) doesn't conflict with anything on the server
8. Confirm project-scoped ICM roles needed — a `sim-tuner` role (like year-zero's `optimiser`) for balance-testing the engine after v1 ships?
