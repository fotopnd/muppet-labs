## Project Name
gridiron

## Description
Add three new hooks to `web/src/api/hooks.ts` that the conference page and scoreboard widget need: a full-game-state ticker hook, a conglomerate list hook, and a single-conglomerate standings hook.

## Language(s)
TypeScript

## Background / Current State

`hooks.ts` currently has:
- `useTickerScoreboard()` — subscribes to the SSE ticker (`/stream/ticker`) and builds `Map<gameId, LiveScore>`. `LiveScore` only stores `score_home, score_away, quarter, possession`. It discards `down, distance, field_pos_after, play_number, description, play_type, yards_gained`.
- `useAllStandings()` — fetches all 5 conglomerates' standings via `useQueries` (5 parallel requests). Overkill when a single conference page only needs one.
- No hook for `GET /conglomerates` (list of all 5 conglomerates with colors).
- No hook for `GET /conglomerates/{id}/standings` (single conglomerate).

The `SsePlayEvent` type in `web/src/types/index.ts` already has all the fields needed for the scoreboard widget — it just isn't being stored wholesale by any hook.

The `ConglomerateOut` and `ConglomerateStandings` types already exist in `web/src/types/index.ts`.

## Success Criteria

Three hooks added to `web/src/api/hooks.ts`, exported alongside the existing hooks:

**1. `useTickerGameState(): Map<number, SsePlayEvent>`**
- Same SSE subscription as `useTickerScoreboard()` (reuse `useTickerStream`)
- Stores the full last `SsePlayEvent` per `game_id` in state
- Returns `Map<number, SsePlayEvent>` — empty map when no events yet

**2. `useAllConglomerates(): UseQueryResult<ConglomerateOut[]>`**
- Fetches `GET /conglomerates`
- Uses `apiFetch<ConglomerateOut[]>('/conglomerates')`
- `queryKey: ['conglomerates']`
- No refetch interval (conglomerate data is static)

**3. `useConglomerateStandings(id: number, options?: { enabled?: boolean }): UseQueryResult<ConglomerateStandings>`**
- Fetches `GET /conglomerates/{id}/standings`
- `queryKey: ['conglomerate', id, 'standings']`
- Respects `enabled` option (needed when id isn't known yet)
- No refetch interval

## Constraints

- Do not modify any existing hook signatures or behaviour
- Do not add new types — `SsePlayEvent`, `ConglomerateOut`, `ConglomerateStandings` are all already in `web/src/types/index.ts`
- Import `ConglomerateOut` and `ConglomerateStandings` from `@/types` at the top of `hooks.ts` alongside existing type imports

## Out of Scope

- `web/src/components/ScoreboardWidget.tsx` (unit 01b)
- `web/src/pages/ConferencePage.tsx` (unit 02)
- `web/src/App.tsx` (unit 03)
- `web/src/pages/Home.tsx` (unit 03)
- `web/src/types/index.ts` — do not modify; all needed types already exist

## Assumptions

- `GET /conglomerates` exists in the backend and returns `ConglomerateOut[]` (confirmed — `conglomerates.py` router)
- `GET /conglomerates/{id}/standings` exists and returns `ConglomerateStandings` (confirmed)
- `SsePlayEvent` has all required fields for the scoreboard widget (confirmed — types/index.ts line 194–211)

## Handoff

Commit to branch `sprint/gridiron/01a-ticker-and-conglomerate-hooks`.

The conference page (unit 02) imports `useTickerGameState`, `useAllConglomerates`, and `useConglomerateStandings` from `@/api/hooks`.
