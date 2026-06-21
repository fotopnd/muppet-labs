# Planner Output — gridiron-live-stats-broadcast

**Sequence:** add-feature | **Role:** planner  
**Date:** 2026-06-21  
**Source brief:** `roles/brief/archive/2026-06-21-gridiron-live-stats-broadcast-brief.md`  
**Resources loaded:** `vibecoding-style.md`, `python-conventions.md`, `typescript-conventions.md`

---

## Project

**gridiron-live-stats-broadcast** — Progressive in-game stats that count up as a game is broadcast, a live multi-game scoreboard with quick-switch navigation, and spoiler prevention for completed game scores on the schedule page.

---

---

## Confirmed Assumptions (from brief)

**A1 — Ticker SSE already carries all game events.** Confirmed. The orchestrator pushes every play from every game to `ticker_queues` (orchestrator.py line 94). Each payload includes `game_id`, `score_home`, `score_away`, `quarter`, `possession`, `play_number`. The scoreboard does not need a polling endpoint — it derives live scores directly from the existing ticker stream.

**A2 — `games.home_score / away_score` are NULL during live play.** Confirmed. The engine only writes these in `UPDATE games SET status='complete'...` at game end. The schedule endpoint returns `null` for live game scores. Live scores must come from SSE.

**A3 — QB player ID is not stored in `play_log`.** Confirmed. `primary_player_id` on `PASS_COMPLETE` is the receiver. For live pass stats, the plan approximates: credit all `PASS_COMPLETE` yards to the top QB per team (`position='QB' ORDER BY alpha DESC LIMIT 1`). Accurate for single-starter teams; acceptable for v1.

**A4 — Frontend stat computation not viable.** QB stats cannot be computed on the frontend alone. Backend serves the live boxscore.

**A5 — No new npm packages.** Confirmed.

---

## Requirements

### Feature 1 — Progressive Boxscore

1. `GET /games/{id}/boxscore` applies the same time gate as the plays endpoint — `max_play = floor(elapsed_seconds / EMIT_INTERVAL)` — when the game is `live` and `replay_started_at` is set. For `complete` games the existing behaviour (read from `player_game_stats`) is unchanged.
2. For live games, boxscore is computed from `play_log` aggregates (not `player_game_stats`). Rush: `play_type IN ('RUSH','TACKLE_FOR_LOSS')` grouped by `primary_player_id`. Receiving: `play_type IN ('PASS_COMPLETE','PASS_INCOMPLETE','PASS_DEFLECTION')` grouped by `primary_player_id`. Both filtered to `play_number <= max_play`.
3. Passing stats are approximated: look up top QB per team (`position='QB' ORDER BY alpha DESC LIMIT 1`), credit that player with total pass yards/completions/attempts for all pass plays by their team within `max_play`.
4. TDs are excluded from the live boxscore in v1 (attribution cannot be reliably derived from `play_log` without engine changes).
5. The endpoint returns the existing `GameBoxscore` schema — no schema change required.
6. `Gamecast.tsx` refetches the boxscore from the API whenever incoming SSE play count crosses a multiple of 5, or when the arriving play type is `TOUCHDOWN` or `FIELD_GOAL_ATTEMPT`.

### Feature 2 — Live Scoreboard and Multi-Game Switching

7. A `useTickerScoreboard()` hook subscribes to `/stream/ticker` using the existing `useTickerStream` pattern and maintains `Map<number, LiveScore>` in state, where `LiveScore = { game_id, score_home, score_away, quarter, possession }`.
8. `WeekSchedule.tsx` calls `useTickerScoreboard()` and overlays live scores from the map onto game cards for `status='live'` games, replacing the `null` API values.
9. Live game cards display current quarter and which team has possession.
10. `GET /live/leaders` returns the top 5 passers, rushers, and receivers across all currently-live games, computed from `play_log` with per-game time gate applied. Excludes TDs. Returns `LiveLeaders` schema (new).
11. `WeekSchedule.tsx` calls `useLiveLeaders()` (30-second poll, only when at least one game is live) and renders a compact leaders section above the game grid.

### Feature 3 — Spoiler Prevention

12. `WeekSchedule.tsx` holds `revealedGames: Set<number>` in `useState` (session-local; not persisted).
13. `GameCard.tsx` accepts `liveScore?: LiveScore`, `revealed?: boolean`, and `onReveal?: () => void` props.
14. Complete game cards with `revealed=false` show "FINAL · tap to reveal" instead of the score. Tapping adds the game to `revealedGames` and navigates to the Gamecast.
15. Complete game cards with `revealed=true` show the final score (existing behaviour).
16. Live game cards always show the current score from `liveScore` (never hidden).
17. Scheduled game cards show no score (unchanged).
18. The Gamecast page for a complete game always shows the final score regardless of schedule-page reveal state.

---

## Technology Stack

| Concern | Choice | Reason |
|---|---|---|
| Language (backend) | Python 3.12 | Existing |
| Language (frontend) | TypeScript 5.x, React 18 | Existing |
| Package managers | uv (backend), pnpm (frontend) | Existing |
| API framework | FastAPI + asyncpg | Existing |
| Frontend server state | TanStack Query | Existing |
| Frontend SSE state | `useRef` + `useState` | Existing `useTickerStream` pattern |
| Styling | Tailwind v4 | Existing |
| New packages | None | Requirement |

---

## File and Module Structure

Changes are scoped to existing files only. No new files.

### Backend

```
gridiron/api/schemas.py
  LiveLeader             — new: { player_id, name, program_name, program_emoji,
                                  game_id, yards }
  LiveLeaders            — new: { passers, rushers, receivers: list[LiveLeader] }

gridiron/api/routers/games.py
  game_boxscore()        — extend: branch on status='live', apply time gate,
                           compute rush + receiving + passing from play_log.
                           Complete-game path unchanged.

gridiron/api/routers/leaderboards.py
  GET /live/leaders      — new endpoint: aggregate rush/rec/pass leaders across
                           all live games from play_log with per-game time gate.
```

### Frontend

```
web/src/types/index.ts
  LiveScore              — new: { game_id, score_home, score_away, quarter, possession }
  LiveLeader             — new (mirrors backend)
  LiveLeaders            — new

web/src/api/hooks.ts
  useTickerScoreboard()  — new: wraps useTickerStream, returns Map<number, LiveScore>
  useLiveLeaders()       — new: GET /live/leaders, refetchInterval: 30_000,
                           enabled only when at least one live game is present

web/src/pages/Gamecast.tsx
  — SSE handler counts incoming plays; useEffect refetches boxscore via apiFetch
    + setState when count % 5 === 0 or play_type is TOUCHDOWN/FIELD_GOAL_ATTEMPT

web/src/components/GameCard.tsx
  — new props: liveScore?, revealed?, onReveal?
  — live → show liveScore; complete+!revealed → reveal UI; complete+revealed → score;
    scheduled → no score

web/src/pages/WeekSchedule.tsx
  — useTickerScoreboard(), useLiveLeaders()
  — useState<Set<number>> revealedGames
  — pass liveScore, revealed, onReveal down to each GameCard
  — render LiveLeaders section above game grid when live games present
```

---

## SQL Designs

### Live boxscore — rush (games.py)
```sql
SELECT pll.primary_player_id,
       SUM(CASE WHEN pll.play_type='RUSH' THEN COALESCE(pll.yards_gained,0) ELSE 0 END)::int AS rush_yards,
       COUNT(CASE WHEN pll.play_type='RUSH' THEN 1 END)::int AS rush_attempts
FROM play_log pll
WHERE pll.game_id = :gid
  AND pll.play_type IN ('RUSH','TACKLE_FOR_LOSS')
  AND pll.play_number <= :max_play
GROUP BY pll.primary_player_id
```

### Live boxscore — receiving (games.py)
```sql
SELECT pll.primary_player_id,
       SUM(CASE WHEN pll.play_type='PASS_COMPLETE' THEN COALESCE(pll.yards_gained,0) ELSE 0 END)::int AS receiving_yards,
       COUNT(CASE WHEN pll.play_type='PASS_COMPLETE' THEN 1 END)::int AS receptions,
       COUNT(*)::int AS targets
FROM play_log pll
WHERE pll.game_id = :gid
  AND pll.play_type IN ('PASS_COMPLETE','PASS_INCOMPLETE','PASS_DEFLECTION')
  AND pll.play_number <= :max_play
GROUP BY pll.primary_player_id
```

### Live boxscore — passing (games.py, two queries per team)
```sql
-- Step 1: top QB for a given program_id
SELECT id AS qb_id FROM players
WHERE program_id = :program_id AND position = 'QB'
ORDER BY alpha DESC LIMIT 1

-- Step 2: pass totals for that team's plays up to max_play
SELECT COUNT(CASE WHEN pll.play_type='PASS_COMPLETE' THEN 1 END)::int AS pass_completions,
       COUNT(*)::int AS pass_attempts,
       SUM(CASE WHEN pll.play_type='PASS_COMPLETE' THEN COALESCE(pll.yards_gained,0) ELSE 0 END)::int AS pass_yards
FROM play_log pll
JOIN players pl ON pl.id = pll.primary_player_id
WHERE pll.game_id = :gid
  AND pll.play_type IN ('PASS_COMPLETE','PASS_INCOMPLETE','PASS_DEFLECTION')
  AND pll.play_number <= :max_play
  AND pl.program_id = :program_id
-- credit result to qb_id from Step 1
```

### Live leaders (leaderboards.py — one query per stat type)
```sql
SELECT pl.id AS player_id, pl.last_name AS name,
       pr.name AS program_name, pr.emoji AS program_emoji,
       pll.game_id,
       SUM(COALESCE(pll.yards_gained, 0))::int AS yards
FROM play_log pll
JOIN players pl ON pl.id = pll.primary_player_id
JOIN programs pr ON pr.id = pl.program_id
JOIN games g ON g.id = pll.game_id
WHERE g.status = 'live'
  AND g.replay_started_at IS NOT NULL
  AND pll.play_type = :play_type          -- 'RUSH' | 'PASS_COMPLETE'
  AND pll.play_number <= FLOOR(
        EXTRACT(EPOCH FROM (NOW() - g.replay_started_at)) / :emit_interval
      )::int
GROUP BY pl.id, pl.last_name, pr.name, pr.emoji, pll.game_id
ORDER BY yards DESC
LIMIT 5
```

---

## Open Questions for Implementer

**Q1** — `useTickerScoreboard` identity: multiple tabs each open their own EventSource (one per page load). This is fine in v1.

**Q2** — Complete card tap: when `revealed=false`, replace the `<Link>` wrapper with `<div onClick>` that calls `onReveal()` then `navigate()`. All other statuses keep `<Link>`.

**Q3** — Live leaders section: hide entirely when `Object.keys(scoreboard).length === 0` (no SSE data yet) to avoid flicker on initial load.

**Q4** — `EMIT_INTERVAL` is already imported in `games.py` from `gridiron.engine.constants`. Use the same import — do not hardcode.

**Q5** — The live boxscore runs 5 queries per call (2 rush/rec aggs + 2 QB lookups + 2 pass aggs). Acceptable for v1 concurrency. Flag if it becomes slow.

---

## Handoff

**Next role:** implementer (architect step skipped — SQL and component structure are concrete enough).

**Implementation order:**
1. `gridiron/api/schemas.py` — `LiveLeader`, `LiveLeaders`
2. `gridiron/api/routers/games.py` — live boxscore path
3. `gridiron/api/routers/leaderboards.py` — `GET /live/leaders`
4. `web/src/types/index.ts` — `LiveScore`, `LiveLeader`, `LiveLeaders`
5. `web/src/api/hooks.ts` — `useTickerScoreboard`, `useLiveLeaders`
6. `web/src/components/GameCard.tsx` — spoiler props
7. `web/src/pages/WeekSchedule.tsx` — ticker + leaders + reveal state
8. `web/src/pages/Gamecast.tsx` — boxscore refetch on SSE plays
