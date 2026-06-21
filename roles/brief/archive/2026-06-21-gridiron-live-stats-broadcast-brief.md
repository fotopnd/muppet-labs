## Project Name
gridiron-live-stats-broadcast

## Description
Three tightly coupled features that make the live broadcast experience accurate and spoiler-safe: progressive in-game stats that count up as a game is broadcast, a live scoreboard that lets users switch between concurrent games, and spoiler prevention that hides final results from the schedule view for games still in progress.

## Language(s)
TypeScript (frontend) · Python (backend API)

## Background / Current State

**Stats are written at game end, not incrementally.**
`player_game_stats` is populated by the engine when a game completes. The boxscore endpoint (`GET /games/{id}/boxscore`) reads that table directly. For a live game, it returns the entire game's final stats immediately — the player who scores in Q4 shows those yards in Q1.

**Plays are already time-gated correctly.**
`GET /games/{id}/plays` filters `play_log` by `(NOW() - replay_started_at) / EMIT_INTERVAL` to return only plays that have "aired" so far. This logic exists and works.

**Schedule exposes raw scores for all statuses.**
`/schedule/current` returns `home_score` and `away_score` for every game regardless of whether it's live or complete. A user who opens the schedule while a game is in the third quarter sees the current score, which is fine. But they also see the final score of a game that finished an hour ago if they haven't watched it yet — that is spoiler exposure.

**Multiple games run concurrently.**
During a broadcast window (e.g. `afternoon`), up to 10 games run simultaneously. Users need to navigate between them without losing context, and the platform needs a single view of all live game scores + player stat leaders that updates in real time.

---

## Feature 1 — Progressive In-Game Boxscore

**What it does:** For a live game, stats in the right-hand panel (leaders widget, stat table) should reflect only plays that have been broadcast so far. Stats start at zero and accumulate as plays arrive.

**Done looks like:**
- Opening a live gamecast at play 40 shows stats for plays 1–40 only
- Stats increment in the UI each time the SSE stream delivers a new play
- On game completion, the final boxscore matches `player_game_stats` exactly
- No new boxscore endpoint required on cold load — stats are computed from the already-loaded plays

**Technical approach (assumption — planner to confirm):**
Compute stats on the frontend from `state.plays` rather than fetching the boxscore endpoint for live games. This requires the plays endpoint (and SSE stream) to include `primary_player_id` and `player_name` fields. The engine already records `primary_player_id` in `play_log`. The plays endpoint would need to join `players` to return `last_name`. Stat accumulation logic mirrors what `accumulate_stats()` does in the engine but in TypeScript.

The alternative (backend `?up_to_play=N` param on boxscore) is heavier and adds a polling cycle. Frontend computation is preferred.

**Out of scope:** Defensive stats (sacks, INTs from the defense side) are already partially tracked on the frontend via `sacks` and `ints_def` fields — the brief does not require expanding this coverage beyond what the play list already carries.

---

## Feature 2 — Live Multi-Game Scoreboard & Quick-Switch

**What it does:** A scoreboard view (can replace or augment the current schedule page during a broadcast window) that shows all live games with their current score, current quarter, and possession. Users can tap any game to jump to its Gamecast. The scoreboard auto-updates.

**Done looks like:**
- During a broadcast window, a "LIVE NOW" scoreboard section appears at the top of the schedule/home page showing all concurrently running games
- Each card shows: home/away emoji + name, current score (counting up), current quarter, possession indicator
- Clicking a card navigates to `/games/{id}`
- The scoreboard refreshes on a short polling interval (SSE ticker already exists — check if it can carry score deltas for all games)
- After a game completes, its card moves to a "FINAL" section below the live cards

**Real-time cross-game stat leaders:**
- A `/live/leaders` endpoint (or equivalent) returns top players across all currently live games by passing_yards, rushing_yards, receiving_yards — updated as plays are broadcast
- This should compute from `play_log` filtered by elapsed time (same gate as `GET /games/{id}/plays`) for each live game
- Leaders are shown on the scoreboard page, not inside a single Gamecast
- Leaders update on the same poll cycle as the scoreboard scores

**Technical approach (assumption — planner to confirm):**
The existing SSE ticker (`/stream/ticker`) sends a heartbeat — check whether it already carries per-game score data. If not, the scoreboard can poll `/schedule/current` on a 5-second interval (10 games × 1 request = acceptable, versus adding complexity to the SSE stream). The `/live/leaders` endpoint is new and aggregates across all live games.

---

## Feature 3 — Spoiler Prevention on Schedule/Scoreboard

**What it does:** The schedule page (and any game list) should not reveal final scores for games the user has not chosen to spoil. Live game scores are fine to show (they change, they're the broadcast). Final scores of completed games are the spoiler.

**Done looks like:**
- Games with `status = 'complete'` show scores only behind a revealed state (click/tap to reveal, or a toggle on the page)
- Games with `status = 'live'` show current score freely (it's the broadcast)
- Games with `status = 'scheduled'` show no score (already the case)
- The reveal preference is session-local (no backend persistence required)
- The Gamecast page itself is unaffected — users navigating to `/games/{id}` for a complete game see the final score

**Out of scope:** Per-game persistence of "I've already seen this result." Session-local state is enough for v1.

---

## Constraints

- No new npm packages — existing TanStack Query, Tailwind, and the SSE hook cover UI state and polling
- Backend: no new tables — aggregate from `play_log` using the existing time-gate logic; `player_game_stats` is authoritative for complete games only
- The existing `EMIT_INTERVAL` constant must be the single source of truth for time-gating (already used in plays endpoint)
- Engine is private and must not be changed to support these features — all stat derivation happens at the API or frontend layer

## Out of Scope

- Push notifications for score changes
- User accounts or per-user spoiler preferences persisted to DB
- Defensive stat leaders (sacks, INTs) in the cross-game leaders view (v1 is passing/rushing/receiving only)
- Replay/rewind of a game that already completed

## Assumptions

- Stats can be computed accurately enough on the frontend from `play_log` data; the engine's `accumulate_stats()` logic is simple enough to port to TS
- The plays endpoint join to `players` for `last_name` is acceptable latency-wise (already fetches O(135) rows per game)
- 5-second polling for the scoreboard is acceptable; no WebSocket/SSE upgrade for the scoreboard page in v1
- Spoiler reveal is session-local (a simple `useState<Set<number>>` of revealed game IDs)
- `/live/leaders` computes from `play_log` in real time — acceptable given the query is bounded by the active game count and play count per game

## Handoff

Next role: planner

The planner should produce:
1. A concrete diff list for the plays endpoint (add `player_name` + `primary_player_id` to response)
2. The stat-accumulation TypeScript logic for frontend boxscore (mirrors `accumulate_stats()` in the engine)
3. The `/live/leaders` endpoint spec (SQL, response schema)
4. Schedule/scoreboard page redesign (live cards vs final cards, spoiler reveal component)
5. Confirm or reject the frontend-computation approach for progressive stats vs a backend `up_to_play` param

Confirm assumption: can the SSE ticker carry per-game score updates for all live games simultaneously, or does it need to remain per-game only?
